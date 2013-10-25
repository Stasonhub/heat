# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from heat.common import exception
from heat.engine import watchrule
from heat.engine import resource
from heat.engine.properties import Properties

from heat.openstack.common import log as logging

logger = logging.getLogger(__name__)


class CloudWatchAlarm(resource.Resource):
    properties_schema = {
        'ComparisonOperator': {
            'Type': 'String',
            'AllowedValues': ['GreaterThanOrEqualToThreshold',
                              'GreaterThanThreshold',
                              'LessThanThreshold',
                              'LessThanOrEqualToThreshold'],
            'Description': _('Operator used to compare the specified '
                             'Statistic with Threshold.'),
            'UpdateAllowed': True,
        },
        'AlarmDescription': {
            'Type': 'String',
            'Description': _('Description for the alarm.'),
            'UpdateAllowed': True,
        },
        'EvaluationPeriods': {
            'Type': 'String',
            'Description': _('Number of periods to evaluate over.'),
            'UpdateAllowed': True,
        },
        'MetricName': {
            'Type': 'String',
            'Description': _('Metric name watched by the alarm.')
        },
        'Namespace': {
            'Type': 'String',
            'Description': _('Namespace for the metric.')
        },
        'Period': {
            'Type': 'String',
            'Description': _('Period (seconds) to evaluate over.'),
            'UpdateAllowed': True,
        },
        'Statistic': {
            'Type': 'String',
            'AllowedValues': ['SampleCount',
                              'Average',
                              'Sum',
                              'Minimum',
                              'Maximum'],
            'Description': _('Metric statistic to evaluate.'),
            'UpdateAllowed': True,
        },
        'AlarmActions': {
            'Type': 'List',
            'Description': _('A list of actions to execute when state '
                             'transitions to alarm.'),
            'UpdateAllowed': True,
        },
        'OKActions': {
            'Type': 'List',
            'Description': _('A list of actions to execute when state '
                             'transitions to ok.'),
            'UpdateAllowed': True,
        },
        'Dimensions': {
            'Type': 'List',
            'Description': _('A list of dimensions (arbitrary name/value '
                             'pairs) associated with the metric.')
        },
        'InsufficientDataActions': {
            'Type': 'List',
            'Description': _('A list of actions to execute when state '
                             'transitions to insufficient-data.'),
            'UpdateAllowed': True,
        },
        'Threshold': {
            'Type': 'String',
            'Description': _('Threshold to evaluate against.'),
            'UpdateAllowed': True,
        },
        'Units': {
            'Type': 'String',
            'AllowedValues': ['Seconds',
                              'Microseconds',
                              'Milliseconds',
                              'Bytes',
                              'Kilobytes',
                              'Megabytes',
                              'Gigabytes',
                              'Terabytes',
                              'Bits',
                              'Kilobits',
                              'Megabits',
                              'Gigabits',
                              'Terabits',
                              'Percent',
                              'Count',
                              'Bytes/Second',
                              'Kilobytes/Second',
                              'Megabytes/Second',
                              'Gigabytes/Second',
                              'Terabytes/Second',
                              'Bits/Second',
                              'Kilobits/Second',
                              'Megabits/Second',
                              'Gigabits/Second',
                              'Terabits/Second',
                              'Count/Second',
                              None],
            'Description': _('Unit for the metric.'),
            'UpdateAllowed': True,
        }
    }

    strict_dependency = False
    update_allowed_keys = ('Properties',)

    def handle_create(self):
        wr = watchrule.WatchRule(context=self.context,
                                 watch_name=self.physical_resource_name(),
                                 rule=self.parsed_template('Properties'),
                                 stack_id=self.stack.id)
        wr.store()

    def handle_update(self, json_snippet, tmpl_diff, prop_diff):
        # If Properties has changed, update self.properties, so we
        # get the new values during any subsequent adjustment
        if prop_diff:
            self.properties = Properties(self.properties_schema,
                                         json_snippet.get('Properties', {}),
                                         self.stack.resolve_runtime_data,
                                         self.name)
            loader = watchrule.WatchRule.load
            wr = loader(self.context,
                        watch_name=self.physical_resource_name())

            wr.rule = self.parsed_template('Properties')
            wr.store()

    def handle_delete(self):
        try:
            wr = watchrule.WatchRule.load(
                self.context, watch_name=self.physical_resource_name())
            wr.destroy()
        except exception.WatchRuleNotFound:
            pass

    def handle_suspend(self):
        wr = watchrule.WatchRule.load(self.context,
                                      watch_name=self.physical_resource_name())
        wr.state_set(wr.SUSPENDED)

    def handle_resume(self):
        wr = watchrule.WatchRule.load(self.context,
                                      watch_name=self.physical_resource_name())
        # Just set to NODATA, which will be re-evaluated next periodic task
        wr.state_set(wr.NODATA)

    def FnGetRefId(self):
        return unicode(self.physical_resource_name())

    def physical_resource_name(self):
        return '%s-%s' % (self.stack.name, self.name)


def resource_mapping():
    return {
        'OS::Heat::CWLiteAlarm': CloudWatchAlarm,
    }
