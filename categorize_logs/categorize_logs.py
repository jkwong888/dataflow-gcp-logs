"""
EXAMPLES
--------

# DirectRunner
python user_score.py \
    --output /local/path/user_score/output

# DataflowRunner
python user_score.py \
    --output gs://$BUCKET/user_score/output \
    --runner DataflowRunner \
    --project $PROJECT_ID \
    --region $REGION_ID \
    --temp_location gs://$BUCKET/user_score/temp
"""

# pytype: skip-file

from __future__ import absolute_import
from __future__ import division

import argparse
import csv
import json
import sys
import logging

import apache_beam as beam
from apache_beam.metrics.metric import Metrics
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions


class ParseLogEntry(beam.DoFn):
  """Parses the log entry into a Python dictionary.

  The human-readable time string is not used here.
  """
  def __init__(self):
    # TODO(BEAM-6158): Revert the workaround once we can pickle super() on py3.
    # super(ParseGameEventFn, self).__init__()
    beam.DoFn.__init__(self)
    self.num_parse_errors = Metrics.counter(self.__class__, 'num_parse_errors')

  def process(self, elem):
    try:

      #print(elem)
      row = json.loads(elem)

      # categorize by the kubernetes deployment that generated the log
      try:
        log_labels = row['labels']
        if log_labels is None:
          yield pvalue.TaggedOutput('uncategorized', row)

        log_cat = log_labels['k8s-pod/app_kubernetes_io/instance']

        if log_cat is None:
          yield pvalue.TaggedOutput('uncategorized', row)

        yield (log_cat, row)
      except KeyError:
          yield pvalue.TaggedOutput('uncategorized', row)


    except:  # pylint: disable=bare-except
      # Log and count parse errors
      self.num_parse_errors.inc()
      logging.error('Parse error on "%s"' % elem, sys.exc_info()[0])

# [END extract_and_sum_score]



# [START main]
def run(argv=None, save_main_session=True):
  """Main entry point; defines and runs the user_score pipeline."""
  parser = argparse.ArgumentParser()

  # The default maps to two large Google Cloud Storage files (each ~12GB)
  # holding two subsequent day's worth (roughly) of data.
  parser.add_argument(
      '--input',
      type=str,
      required=True, 
      help='Path to the log bucket')

  parser.add_argument(
      '--output', 
      type=str, 
      required=True, 
      help='Path to the output file(s).')

  args, pipeline_args = parser.parse_known_args(argv)

  options = PipelineOptions(pipeline_args)

  # We use the save_main_session option because one or more DoFn's in this
  # workflow rely on global context (e.g., a module imported at module level).
  options.view_as(SetupOptions).save_main_session = save_main_session

  with beam.Pipeline(options=options) as p:
    logs = (  # pylint: disable=expression-not-assigned
        p
        | 'ReadInputText' >> beam.io.ReadFromText(args.input)
        | 'ParseLogEntry' >> beam.ParDo(ParseLogEntry()).with_outputs(
            'uncategorized',
            main='logs'
          )
    )
        
    categorized, _ = logs
    ( 
      categorized 
        | 'Group' >> beam.GroupByKey()
        | 'getKeys' >> beam.Keys()
        | 'Write' >> beam.io.WriteToText(args.output)
    )

    # TODO write these somewhere
    uncategorized_logs = logs['uncategorized']
    (
      uncategorized_logs
      | 'count uncategorized' >> beam.combiners.Count.Globally()
      | beam.Map(lambda x: print("Uncategorized logs: %d" % x))
    )


# [END main]

if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  run()
