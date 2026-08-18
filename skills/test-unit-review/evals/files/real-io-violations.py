"""Unit tests for ReportExporter.

VIOLATIONS — isolation:
  test_export_pdf_creates_file      : writes to the real filesystem (/tmp)
  test_fetch_template_from_cdn      : sends a real outbound HTTP request
  TestReportExporterWithDB          : setup_method opens a real PostgreSQL connection
"""
import os

import requests
import pytest

from exporters.report_exporter import ReportExporter


def test_export_pdf_creates_file():
    """Exports a report to PDF and verifies the file exists on disk."""
    exporter = ReportExporter()
    path = "/tmp/report_test_output.pdf"
    exporter.export(data={"title": "Q1"}, output_path=path)
    assert os.path.exists(path)   # real filesystem I/O — violates isolation
    os.remove(path)


def test_fetch_template_from_cdn():
    """Downloads a template from the CDN and applies it to an empty data set."""
    exporter = ReportExporter()
    resp = requests.get("https://cdn.example.com/templates/report.html")  # real HTTP call
    assert resp.status_code == 200
    exporter.apply_template(resp.text, data={})


class TestReportExporterWithDB:
    """Integration-style tests embedded in a unit test file — DB is not mocked."""

    def setup_method(self):
        import psycopg2
        # real database connection — not mocked or stubbed
        self.conn = psycopg2.connect(
            "host=localhost dbname=reports user=sa password=sa"
        )

    def test_load_report_data_from_db_returns_row(self):
        """Loads a report row from PostgreSQL and asserts it is not None."""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM reports LIMIT 1")
        row = cur.fetchone()
        assert row is not None   # depends on live database state

    def teardown_method(self):
        self.conn.close()
