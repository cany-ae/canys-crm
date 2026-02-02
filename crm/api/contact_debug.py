
import frappe

def log_contact_type(doc, method):
    frappe.log_error(
        title="Contact Type Debug",
        message="Contact: {} | custom_contact_type: {} | method: {}".format(
            doc.name, doc.custom_contact_type, method
        )
    )
