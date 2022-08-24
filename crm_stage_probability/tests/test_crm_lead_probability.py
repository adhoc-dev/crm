# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.exceptions import UserError
from odoo.tests import TransactionCase


class TestCrmLeadProbability(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.stage_new = cls.env.ref("crm.stage_lead1")
        cls.stage_qualified = cls.env.ref("crm.stage_lead2")
        cls.stage_proposition = cls.env.ref("crm.stage_lead3")
        cls.stage_won = cls.env.ref("crm.stage_lead4")
        cls.opportunity_1 = cls.env.ref("crm.crm_case_32")

    def test_update_probability(self):
        self.assertEqual(self.opportunity_1.stage_id, self.stage_qualified)
        self.assertFalse(self.opportunity_1.is_automated_probability)
        self.assertFalse(self.opportunity_1.is_stage_probability)
        self.opportunity_1.write({"stage_id": self.stage_new.id})
        self.assertEqual(self.opportunity_1.probability, self.stage_new.probability)
        self.assertFalse(self.opportunity_1.is_automated_probability)
        self.assertTrue(self.opportunity_1.is_stage_probability)
        self.opportunity_1.write({"stage_id": self.stage_proposition.id})
        self.assertEqual(
            self.opportunity_1.probability, self.stage_proposition.probability
        )
        self.assertFalse(self.opportunity_1.is_automated_probability)
        self.assertTrue(self.opportunity_1.is_stage_probability)
        self.opportunity_1.write({"probability": 31.56})
        self.assertFalse(self.opportunity_1.is_automated_probability)
        self.assertFalse(self.opportunity_1.is_stage_probability)
        self.opportunity_1.action_set_stage_probability()
        self.assertEqual(
            self.opportunity_1.probability, self.opportunity_1.stage_id.probability
        )
        self.assertTrue(self.opportunity_1.is_stage_probability)

    def test_create_opportunity(self):
        opportunity = self.env["crm.lead"].create(
            {"name": "My opportunity", "type": "opportunity"}
        )
        default_stage_id = (
            self.env["crm.lead"]._stage_find(domain=[("fold", "=", False)]).id
        )
        default_stage = self.env["crm.stage"].browse(default_stage_id)
        self.assertEqual(opportunity.probability, default_stage.probability)
        self.assertFalse(opportunity.is_automated_probability)

    def test_create_opportunity_default_stage_id(self):
        opportunity = (
            self.env["crm.lead"]
            .with_context(default_stage_id=self.stage_qualified.id)
            .create({"name": "My opportunity", "type": "opportunity"})
        )
        self.assertEqual(opportunity.probability, self.stage_qualified.probability)
        self.assertFalse(opportunity.is_automated_probability)

    def test_mass_update(self):
        all_stages = self.env["crm.stage"].search([])
        self.assertTrue(all(all_stages.mapped("on_change")))
        wiz = (
            self.env["crm.lead.stage.probability.update"]
            .with_context(active_ids=all_stages.ids)
            .create({})
        )
        wiz.execute()
        all_leads = self.env["crm.lead"].search([])
        self.assertTrue(all(all_leads.mapped("is_stage_probability")))
        self.assertFalse(all(all_leads.mapped("is_automated_probability")))
        new_line = wiz.crm_stage_update_ids.filtered(
            lambda x: x.stage_id == self.stage_new
        )
        self.assertEqual(new_line.lead_count, 13)
        won_line = wiz.crm_stage_update_ids.filtered(
            lambda x: x.stage_id == self.stage_won
        )
        self.assertEqual(won_line.lead_count, 3)

    def test_mass_update_no_onchange_stage(self):
        new_stage = self.env["crm.stage"].create(
            {
                "name": "No Onchange",
                "sequence": 10,
            }
        )
        self.assertFalse(new_stage.on_change)
        with self.assertRaises(UserError) as context:
            (
                self.env["crm.lead.stage.probability.update"]
                .with_context(active_ids=new_stage.ids)
                .create({})
            )
        self.assertTrue("Following stages must be set as" in str(context.exception))
