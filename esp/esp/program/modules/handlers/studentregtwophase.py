__author__    = "MIT ESP"
__date__      = "$DATE$"
__rev__       = "$REV$"
__license__   = "GPL v.2"
__copyright__ = """
This file is part of the ESP Web Site
Copyright (c) 2013 MIT ESP

The ESP Web Site is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

Contact Us:
ESP Web Group
MIT Educational Studies Program,
84 Massachusetts Ave W20-467, Cambridge, MA 02139
Phone: 617-253-4882
Email: web@esp.mit.edu
"""

import datetime
import simplejson

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect, HttpResponse

from esp.cal.models import Event
from esp.middleware.threadlocalrequest import get_current_request
from esp.program.models import ClassCategories, ClassSection, ClassSubject, RegistrationType, StudentRegistration, StudentSubjectInterest
from esp.program.modules.base import ProgramModuleObj, main_call, aux_call, meets_deadline, needs_student, meets_grade
from esp.users.models import Record
from esp.web.util import render_to_response

class StudentRegTwoPhase(ProgramModuleObj):

    def isCompleted(self):
        records = Record.objects.filter(user=get_current_request().user,
                                        event="twophase_reg_done",
                                        program=self.program)
        return records.count() != 0

    @classmethod
    def module_properties(cls):
        return {
            "link_title": "Two-Phase Student Registration",
            "admin_title": "Two-Phase Student Registration",
            "module_type": "learn",
            "seq": 5,
            "required": True
            }

    @main_call
    @needs_student
    @meets_grade
    @meets_deadline('/Classes/Lottery')
    def studentreg2phase(self, request, tl, one, two, module, extra, prog):
        """
        Serves the two-phase student reg page. This page includes instructions
        for registration, and links to the phase1/phase2 sub-pages.
        """

        timeslot_dict = {}
        # Populate the timeslot dictionary with the priority to class title
        # mappings for each timeslot.
        priority_regs = StudentRegistration.valid_objects().filter(
            user=request.user, relationship__name__startswith='Priority')
        priority_regs = priority_regs.values(
            'relationship__name', 'section', 'section__parent_class__title')
        for student_reg in priority_regs:
            rel = student_reg['relationship__name']
            title = student_reg['section__parent_class__title']
            sec = ClassSection.objects.get(pk=student_reg['section'])
            times = sec.meeting_times.all().order_by('start')
            if times.count() == 0:
                continue
            timeslot = times[0].id
            if not timeslot in timeslot_dict:
                timeslot_dict[timeslot] = {rel: title}
            else:
                timeslot_dict[timeslot][rel] = title

        # Iterate through timeslots and create a list of tuples of information
        prevTimeSlot = None
        blockCount = 0
        schedule = []
        timeslots = prog.getTimeSlots(types=['Class Time Block', 'Compulsory'])
        for i in range(len(timeslots)):
            timeslot = timeslots[i]
            if prevTimeSlot != None:
                if not Event.contiguous(prevTimeSlot, timeslot):
                    blockCount += 1

            if timeslot.id in timeslot_dict:
                priority_dict = timeslot_dict[timeslot.id]
                priority_list = sorted(priority_dict.items())
                schedule.append((timeslot, priority_list, blockCount + 1))
            else:
                schedule.append((timeslot, {}, blockCount + 1))

            prevTimeSlot = timeslot

        context = {}
        context['timeslots'] = schedule

        return render_to_response(
            self.baseDir()+'studentregtwophase.html', request, context)

    def catalog_context(self, request, tl, one, two, module, extra, prog):
        """
        Builds context specific to the catalog. Used by all views which render
        the catalog. This is not a view in itself.
        """
        context = {}
        # FIXME(gkanwar): This is a terrible hack, we should find a better way
        # to filter out certain categories of classes
        context['open_class_category_id'] = prog.open_class_category.id
        context['lunch_category_id'] = ClassCategories.objects.get(category='Lunch').id
        return context

    @aux_call
    @needs_student
    @meets_grade
    @meets_deadline('/Classes/Lottery')
    def mark_classes(self, request, tl, one, two, module, extra, prog):
        """
        Displays a filterable catalog which allows starring classes that the
        user is interested in.
        """
        # get choices for filtering options
        context = {}

        def group_columns(items):
            # collect into groups of 5
            cols = []
            for i, item in enumerate(items):
                if i % 5 == 0:
                    col = []
                    cols.append(col)
                col.append(item)
            return cols

        category_choices = []
        for category in prog.class_categories.all():
            category_choices.append((category.id, category.category))
        context['category_choices'] = group_columns(category_choices)

        grade_choices = []
        grade_choices.append(('ALL', 'All'))
        for grade in range(prog.grade_min, prog.grade_max + 1):
            grade_choices.append((grade, grade))
        context['grade_choices'] = group_columns(grade_choices)

        catalog_context = self.catalog_context(
            request, tl, one, two,module, extra, prog)
        context.update(catalog_context)

        return render_to_response(self.baseDir() + 'mark_classes.html', request, context)

    @aux_call
    @needs_student
    @meets_grade
    @meets_deadline('/Classes/Lottery')
    def mark_classes_interested(self, request, tl, one, two, module, extra, prog):
        """
        Saves the set of classes marked as interested by the student.

        Ex: request.POST['json_data'] = {
            'interested': [1,5,3,9],
            'not_interested': [4,6,10]
        }
        """
        if not 'json_data' in request.POST:
            return HttpResponseBadRequest('JSON data not included in request.')
        try:
            json_data = simplejson.loads(request.POST['json_data'])
        except ValueError:
            return HttpResponseBadRequest('JSON data mis-formatted.')
        if not isinstance(json_data.get('interested'), list) or \
           not isinstance(json_data.get('not_interested'), list):
            return HttpResponseBadRequest('JSON data mis-formatted.')

        # Determine which of the given class ids are valid
        valid_ids = ClassSubject.objects.filter(
            pk__in=json_data['interested'],
            parent_program=prog,
            status__gte=0).values_list('pk', flat=True)
        # Unexpire any matching SSIs that exist already (to avoid
        # creating duplicate objects).
        to_unexpire = StudentSubjectInterest.objects.filter(
            user=request.user,
            subject__pk__in=valid_ids)
        to_unexpire.update(end_date=None)
        # Determine which valid ids haven't had SSIs created yet
        # and bulk create those objects.
        existing_ids = to_unexpire.values_list('subject__pk', flat=True)
        to_create_ids = set(valid_ids) - set(existing_ids)
        StudentSubjectInterest.objects.bulk_create([
            StudentSubjectInterest(
                user=request.user,
                subject_id=subj_id)
            for subj_id in to_create_ids])
        # Expire any matching SSIs that are in 'not_interested'
        to_expire = StudentSubjectInterest.objects.filter(
            user=request.user,
            subject__pk__in=json_data['not_interested'])
        to_expire.update(end_date=datetime.datetime.now())

        return HttpResponse()

    @aux_call
    @needs_student
    @meets_grade
    @meets_deadline('/Classes/Lottery')
    def rank_classes(self, request, tl, one, two, module, extra, prog):
        """
        Displays a filterable catalog including only class subjects for which
        the student has a StudentSubjectInterest. The sticky on top
        of the catalog lets the student order the top N priorities of classes
        for this particular timeslot. The timeslot is specified through extra.
        """
        timeslot = Event.objects.get(pk=int(extra), program=prog)
        context = dict()
        context['timeslot'] = timeslot
        context['num_priorities'] = prog.priorityLimit()
        context['priorities'] = range(1,prog.priorityLimit()+1)

        catalog_context = self.catalog_context(
            request, tl, one, two,module, extra, prog)
        context.update(catalog_context)

        return render_to_response(
            self.baseDir() + 'rank_classes.html', request, context)

    @aux_call
    @needs_student
    @meets_grade
    @meets_deadline('/Classes/Lottery')
    def save_priorities(self, request, tl, one, two, module, extra, prog):
        """
        Saves the priority preferences for student registration phase 2.
        """
        # Guard against missing json_data (the save and go back button will
        # leave json_data blank if not dirty)
        if not 'json_data' in request.POST:
            return HttpResponseRedirect('/learn/'+prog.getUrlBase()+'/studentreg')

        data = simplejson.loads(request.POST['json_data']);
        timeslot_id = data.keys()[0]
        priorities = data[timeslot_id]
        rel_names = ['Priority/%s'%p for p in priorities.keys()]
        # Pull up the registrations that exist (including expired ones)
        srs = StudentRegistration.objects.filter(
            user=request.user, section__parent_class__parent_program=prog,
            relationship__name__in=rel_names,
            section__meeting_times__id__exact=timeslot_id)
        srs = srs.order_by('relationship__name')
        # Modify the existing registrations as needed to ensure the section
        # is correct, and they are unexpired
        for (sr, p) in zip(srs, sorted(priorities.keys())):
            # If blank, we are removing priority
            if priorities[p] == '':
                sr.expire()
                continue
            sec_id = int(priorities[p])

            should_save = False
            if sr.section.id != sec_id:
                sr.section = ClassSection.objects.get(
                    parent_class=sec_id,
                    meeting_times__id__exact=timeslot_id)
                should_save = True
            if not sr.is_valid():
                sr.unexpire(save=False)
                should_save = True
            if should_save:
                sr.save()
        # Create registrations that need to be created
        rel_existing_names = srs.values_list('relationship__name', flat=True)
        rel_existing = [r.split('/')[1]
                        for r in rel_existing_names]
        rel_create = set(priorities.keys()) - set(rel_existing)
        for rel_index in rel_create:
            rel, created = RegistrationType.objects.get_or_create(
                name='Priority/%s' % rel_index)
            try:
                sec = ClassSection.objects.get(
                    parent_class=int(priorities[rel_index]),
                    meeting_times__id__exact=timeslot_id)
            except ValueError as e:
                # Catch having an empty string for the priority
                # (nothing selected)
                continue
            except ObjectDoesNotExist as e:
                # TODO(gkanwar): Indicate to the caller what failed in some
                # way that's better than silently ignoring them.
                continue
            sr = StudentRegistration(
                user=request.user,
                section=sec,
                relationship=rel)
            sr.save()

        return HttpResponseRedirect('/learn/'+prog.getUrlBase()+'/studentreg')

    class Meta:
        abstract = True
