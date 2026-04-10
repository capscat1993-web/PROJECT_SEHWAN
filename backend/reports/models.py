from django.db import models


class ReportImport(models.Model):
    source_file = models.TextField()
    company_name = models.TextField(blank=True, null=True)
    representatives = models.TextField(blank=True, null=True)
    biz_no = models.TextField(blank=True, null=True)
    report_date = models.TextField(blank=True, null=True)
    imported_at = models.TextField()
    industry = models.TextField(blank=True, null=True)
    main_product = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "report_imports"


class ReportNote(models.Model):
    import_ref = models.ForeignKey(
        ReportImport,
        models.DO_NOTHING,
        db_column="import_id",
        related_name="notes",
    )
    row_no = models.IntegerField()
    section = models.TextField()
    line = models.TextField()

    class Meta:
        managed = False
        db_table = "report_notes"


class ReportValue(models.Model):
    import_ref = models.ForeignKey(
        ReportImport,
        models.DO_NOTHING,
        db_column="import_id",
        related_name="values",
    )
    row_no = models.IntegerField()
    section = models.TextField()
    unit = models.TextField(blank=True, null=True)
    metric = models.TextField()
    period = models.TextField(blank=True, null=True)
    submetric = models.TextField(blank=True, null=True)
    category = models.TextField(blank=True, null=True)
    value_raw = models.TextField(blank=True, null=True)
    value_num = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "report_values"
