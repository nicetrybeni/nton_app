from . import __version__ as app_version

app_name = "nton_app"
app_title = "NTON App"
app_publisher = "Raya"
app_description = "Nature to Nurture App with Frappe"
app_email = "lbencio@rayasolutionsph.com"
app_license = "MIT"

doc_events = {
    "Shopify Setting": {
        "after_save": "nton_app.hooks.after_save"
    }
}

# fixtures = ["Custom Field", "Client Script"]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/nton_app/css/nton_app.css"
# app_include_js = "/assets/nton_app/js/nton_app.js"

# include js, css files in header of web template
# web_include_css = "/assets/nton_app/css/nton_app.css"
# web_include_js = "/assets/nton_app/js/nton_app.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "nton_app/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
#	"methods": "nton_app.utils.jinja_methods",
#	"filters": "nton_app.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "nton_app.install.before_install"
# after_install = "nton_app.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "nton_app.uninstall.before_uninstall"
# after_uninstall = "nton_app.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "nton_app.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
#	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
#	"*": {
#		"on_update": "method",
#		"on_cancel": "method",
#		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------
# "nton_app.lazada_tasks.update_stock"
### part of "0 * * * *" and "*/40 * * * *"

# "nton_app.lazada_tasks.cron",
### temporarily disconnected (while under testing)
### part of "0 3 * * *"

# "nton_app.lazada_tasks.clean_logs",
### part of "0 1 * * *"

scheduler_events = {
    "cron": {
		"0 * * * *" : [
			
		],

		"*/40 * * * *" : [
		],

        "0 1 * * *" : [
			"nton_app.lazada_tasks.generate_new_token"
		],
        "0 3 * * *": [
			"nton_app.tiktokshop_api.bill_remittances",
			"nton_app.shopee_api.get_remittances",
        ],
		
		
    }
    
	# COMMENTED FROM hooks.py
	# "0 3,*/120 * * *" : [
	# 		"nton_app.tiktokshop_setup.refresh_token",
	# 	],
	# 	"0 */3 * * *" : [
	# 		"nton_app.shopee_api.test_shopee_refresh",
	# 		"nton_app.shopee_api.shopee_refresh"
	# 	],
 
	# "*/40 * * * *" : [
	# 	"nton_app.shopee_api.cron_update_stocks",
	# 	"nton_app.tiktokshop_api.cron_update_stocks",
	# ],
	# "0 */3 * * *" : [
	# 		"nton_app.shopee_api.test_shopee_refresh",
	# 		"nton_app.shopee_api.shopee_refresh",
	# 		"nton_app.shopee_api.cron_update_stocks",
	# 		"nton_app.tiktokshop_api.cron_update_stocks"
	# 	],
    
	# "all": [
	# 	"nton_app.tasks.all"
	# ],
	# "daily": [
	# 	"nton_app.tasks.daily"
	# ],
	# "hourly": [
	# 	"nton_app.tasks.hourly"
	# ],
	# "weekly": [
	# 	"nton_app.tasks.weekly"
	# ],
	# "monthly": [
	# 	"nton_app.tasks.monthly"
	# ],
}

# Testing
# -------

# before_tests = "nton_app.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "nton_app.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "nton_app.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["nton_app.utils.before_request"]
# after_request = ["nton_app.utils.after_request"]

# Job Events
# ----------
# before_job = ["nton_app.utils.before_job"]
# after_job = ["nton_app.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
#	{
#		"doctype": "{doctype_1}",
#		"filter_by": "{filter_by}",
#		"redact_fields": ["{field_1}", "{field_2}"],
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_2}",
#		"filter_by": "{filter_by}",
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_3}",
#		"strict": False,
#	},
#	{
#		"doctype": "{doctype_4}"
#	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"nton_app.auth.validate"
# ]
