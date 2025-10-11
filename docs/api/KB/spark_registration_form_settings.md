# Registration Form Settings

There are a number of configuration options for each registration form that will allow you to automatically log information for each new registrant. To access the registration form settings from the Forms page, click on the appropriate micromenu and click Settings. If you are already on the form template page in Carpenter, click Settings.

## Available Fields and Options

| Name | Description |
|------|-------------|
| **Form Name** | The name of the registration form. For example, you may have several versions of the form depending on how a registrant enters the database, so your forms could be named "Registration Form - Website," "Registration Form - Sales Centre," etc. |
| **Registration Source** | The way in which the registrant entered the database. Choose a registration source from the drop-down list. |
| **Permalink** | Choose a permalink that is unique to your project. For example, if your form is named "Registration Form - Website" you might use "projectname-registration-form-website" as your permalink. Be sure that your permalink contains only lowercase letters, numbers, dashes (-), and underscores (_). |
| **Redirect Success** | By default, successful registrants will be directed to a generic Spark success page, but you can direct successful registrants to a webpage by entering the full URL (must include http). This allows registrants to be directed to a custom, project-branded page. |
| **Redirect Error** | By default, unsuccessful registrants will be directed to the Spark-hosted version of the form you are using, but you can direct unsuccessful registrants to a webpage by entering the full URL (must include http). |
| **Registration Form Type** | Select how the registration form will be used. Web Registration indicates the registrant is entering the database from an online form, whereas On Site indicates they are registering at the sales centre. Survey indicates a form that was used as a survey to collect additional information about registrants, often sent by email. |
| **Interaction Type** | Choose which interaction will be logged when a contact registers through the form. If there isn't an appropriate interaction type, ask an administrator to create one. |
| **Recaptcha** | Indicates whether submissions to this form's URL should be accepted without a recaptcha response. This is only for users who are creating custom forms from the raw HTML and have added the Google Recaptcha widget. Do not toggle this setting on if you are using an iFrame, the Spark-hosted form or your form does not contain this widget because none of your submissions will post successfully. |
| **Assigned Ratings** | Select which rating to apply to registrants using the form. If the form includes the agent section, you can choose to apply one rating to agents and another rating to all other contacts. Regardless of the ratings you choose, anyone indicating they are an agent will receive the agent tag. |
| **Auto Reply Email Template** | Fill in the from address and name, choose an email template to automatically send to successful registrants and fill in the subject line field. If this section is left blank, no email will be sent. Note: if anyone replies to the auto email, the reply will be directed to the from address, so be sure to use a valid, monitored email. |
| **Auto Assignment to Team Members** | Choose to assign new registrants using the form to a specific team member or to assign to a group of team members on a rotating basis (team members must have auto assign turned on in Team Settings to be included in the rotation). If no assignment is chosen, the registrants will not be assigned. |
| **Notification Emails** | Choose a team member to be notified each time someone registers using the form. If no team member is selected, users will not be notified of new registrants by email. |

---
*Source: https://knowledge.spark.re/registration-form-settings*