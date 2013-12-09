from django.db import models

class MyTestModel(models.Model):
    field1 = models.CharField(max_length=200)
    field2 = models.DateTimeField('date published')

    def was_published_recently(self):
        return True

    def test(self):
        return False

    was_published_recently.admin_order_field = 'field2'
    was_published_recently.boolean = True
    was_published_recently.short_description = 'Published recently?'


class MyRelatedTestModel(models.Model):
    my_test_model = models.ForeignKey(MyTestModel)
    description = models.CharField(max_length=200)
    count = models.IntegerField(default=0)

    def was_published_recently(self):
        return self.count * 5
