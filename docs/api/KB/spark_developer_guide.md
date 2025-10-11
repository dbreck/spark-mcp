# Registration Form Developer Guide

If you choose to have a web developer make a custom registration page for your project, be sure to send them this guide. Depending on your specifications, your web developer may write most of the form from scratch, but there are a few things they must keep in mind to ensure the form data submits to Spark successfully.

## Getting the Raw Form Code

As a web developer, the first thing you'll need is the raw form code. If you don't have access to the project on Spark and your client has not yet provided you with this, please get in touch with them and either request that they add you as a Web Developer to the project, or have them send you the code. If you already have access to the project, you can find the code under **Embed Options** in each form's micromenu.

## Critical Requirements

The two things you **must not change** about this code are the form tags; specifically:

1. **Form Action**: It must POST to the url specified in the `action` attribute
2. **Field Names**: The `name` attributes on any of the form field tags must be kept intact

You can remove as many fields as you like (except `"contact[email]"` which is necessary for a successful submission), change the labels and aesthetically restructure it to meet client specifications, but those two things must stay the same.

### Example Form Tag
```html
<form accept-charset="UTF-8"
      action="https://spark.re/your-company/your-project/register/form-id"
      id="register-form"
      method="post">
```

### Example Input Tag
```html
<input id="contact_email" name="contact[email]" type="email" />
```

## Redirecting

You need to indicate where to redirect the user after they have successfully (or unsuccessfully) submitted the form. Most clients build a simple Thank You page as their `redirect_success` and use the url of the page where you are hosting the form as the `redirect_error`. Enter these urls as the value for the hidden inputs as below.

### Example Redirects
```html
<input id="redirect_success" name="redirect_success" type="hidden"
       value="http://yourproject.com/your_thank_you_page.html" />

<input id="redirect_error" name="redirect_error" type="hidden"
       value="http://yourproject.come/register_link" />
```

## Validation

We do not post any of the data back to the redirect error url. To avoid contacts filling out a long form, only to be redirected to an empty one after an unsuccessful submission, we provide basic validation for Email and any other required fields. If further validation is required, you must add it to the custom registration form.

## Spam and Recaptcha

Spark forms include a basic spam trap that filters out most unwanted requests. The `"are_you_simulated"` input is hidden via javascript on page load, so that the typical javascript-enabled user will not see it. Most bots do not have javascript enabled and will blindly fill out every field on the form. If the form is submitted with a value in that field, then it is assumed to be spam and is rejected by our servers.

If, however, a registration page is targeted by a more clever spambot, you may need to implement a more robust solution. Spark also provides support for **Recaptcha V3**. When you register for the Recaptcha API, you will receive a pair of keys. Implement the captcha as per their Developer's Guide and then supply your client with the Site key and the Secret key, which they will need to enter in their [Recaptcha Setup](https://knowledge.spark.re/anti-spam) (under Forms → Registration Forms) on Spark.

## Special Fields

### Agent
Your client may choose to use the agent field in their form. This is a special field that, if checked, will assign this registrant an Agent rating on Spark. If your client requests an alternative format for this question (ie: Yes/No radio buttons, or a select tag), please ensure that the alternative options submit null/empty values for this field.

**Default:**
```html
<input id="agent" name="agent" type="checkbox" value="true">
```

**Alternative Example:**
```html
<select id="agent" name="agent">
    <option value> No </option>
    <option value="true"> Yes </option>
</select>
```

### Source
This field is used to specify a custom source for incoming registrants and may already be set if the client has completed the form settings in advance. For example, if you are hosting the form on multiple websites, you can declare a unique source on each form so that the client can identify on Spark which site the contact has registered from.

If this option is excluded, Spark will set the source as "Registration Form."

**Default:**
```html
<input id="source" name="source" type="hidden" value="Registration Form">
```

### Full Name
If your client prefers, you can include a `"full_name"` field in your form instead of using separate first and last name inputs. When the form is submitted to Spark, we will split the value of the full_name field on the first space to populate first and last name. Be sure your client is aware that this may result in a few odd entries in the event that a registrant provides multiple first names or includes their middle name.

**Example:**
```html
<input id="contact_full_name" name="contact[full_name]" type="text" />
```

---

For any further technical inquiries relating to Spark, feel free to contact our tech team at [support@spark.re](mailto:support@spark.re).

---
*Source: https://knowledge.spark.re/registration-form-developer-guide*