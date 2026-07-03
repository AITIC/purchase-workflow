# -*- coding: utf-8 -*-
"""Workaround for an openupgradelib/Odoo 19 incompatibility.

openupgradelib (as of 3.13.4, the latest release) unconditionally looks up
the `base.field_ir_property__value_reference` xmlid inside
`_change_reference_refs_orm`, part of `merge_records()`. The `ir.property`
model was removed from Odoo core in a later version, so that xmlid no
longer exists in v19 and the lookup raises `ValueError`, crashing every
call to `merge_records()` - including this module's own merge action.

This patches just that one lookup to degrade gracefully (skip it, since
there is nothing named that way to migrate anymore) instead of crashing.
Safe to remove once openupgradelib ships a real fix for Odoo 17+.
"""
from openupgradelib import openupgrade_merge_records as _oum


def _change_reference_refs_orm(env, model_name, record_ids, target_record_id, exclude_columns):
    fields = env["ir.model.fields"].search([("ttype", "=", "reference")])
    try:
        fields |= env.ref("base.field_ir_property__value_reference")
    except ValueError:
        pass  # ir.property no longer exists in this Odoo version
    for field in fields:
        try:
            model = env[field.model].with_context(active_test=False)
        except KeyError:
            continue
        field_name = field.name
        if (
            not model._auto
            or not model._fields.get(field_name)
            or not field.store
            or (model._table, field_name) in exclude_columns
        ):
            continue
        expr = ["%s,%s" % (model_name, x) for x in record_ids]
        records = model.search([(field_name, "in", expr)])
        if records:
            records.write({field_name: "%s,%s" % (model_name, target_record_id)})


_oum._change_reference_refs_orm = _change_reference_refs_orm
