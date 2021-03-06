# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-23 12:14
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stores', '0027_auto_20171031_0942'),
    ]

    # Rename the database tables that refer to the models PickupDate,
    # PickupDateSeries and Feedback.
    database_operations = [
        migrations.AlterModelTable('pickupdate', 'pickups_pickupdate'),
        migrations.AlterModelTable('pickupdateseries', 'pickups_pickupdateseries'),
        migrations.AlterModelTable('feedback', 'pickups_feedback'),
    ]

    # Delete the models PickupDate, PickupDateSeries and Feedback.
    # They will be re-created in the new pickups app.
    state_operations = [
        migrations.AlterUniqueTogether(
            name='feedback',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='feedback',
            name='about',
        ),
        migrations.RemoveField(
            model_name='feedback',
            name='given_by',
        ),
        migrations.RemoveField(
            model_name='pickupdate',
            name='collectors',
        ),
        migrations.RemoveField(
            model_name='pickupdate',
            name='series',
        ),
        migrations.RemoveField(
            model_name='pickupdate',
            name='store',
        ),
        migrations.RemoveField(
            model_name='pickupdateseries',
            name='store',
        ),
        migrations.DeleteModel(
            name='Feedback',
        ),
        migrations.DeleteModel(
            name='PickupDate',
        ),
        migrations.DeleteModel(
            name='PickupDateSeries',
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=database_operations,
            state_operations=state_operations)
    ]
