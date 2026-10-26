import json
import sqlite3
import unittest
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]

class OperationsProjectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df=pd.read_csv(ROOT/'data/service_requests.csv')
        cls.payload=json.loads((ROOT/'outputs/dashboard_data.json').read_text())

    def test_request_ids_are_unique(self):
        self.assertEqual(self.df.request_id.nunique(),len(self.df))

    def test_expected_sample_size_and_schema(self):
        self.assertEqual(len(self.df),8200)
        for c in ['created_at','status','priority','service_type','team','sla_target_hours','observed_elapsed_hours']:
            self.assertIn(c,self.df.columns)

    def test_resolved_cases_have_resolution_hours(self):
        res=self.df[self.df.status=='Resolved']
        self.assertTrue(res.resolution_hours.notna().all())
        self.assertTrue(self.df[self.df.status=='Open'].resolved_at.isna().all())

    def test_sla_flags_match_elapsed_and_target(self):
        expected=self.df.observed_elapsed_hours <= self.df.sla_target_hours
        self.assertTrue((expected == self.df.resolution_sla_met_or_not_yet_breached).all())

    def test_attention_scores_are_bounded(self):
        queue=pd.read_csv(ROOT/'outputs/queue_attention_queue.csv')
        self.assertTrue(queue.queue_attention_score.between(0,100).all())

    def test_dashboard_contains_all_rows_and_story_chapters(self):
        self.assertEqual(len(self.payload['rows']),len(self.df))
        html=(ROOT/'index.html').read_text()
        for text in ['The promise','Where work sticks','The next shift','handoffSlider','queueTable']:
            self.assertIn(text,html)

    def test_sqlite_tables_exist(self):
        with sqlite3.connect(ROOT/'outputs/operations_analytics.db') as con:
            names={r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertTrue({'service_requests','request_activity_log'}.issubset(names))

if __name__=='__main__': unittest.main()
