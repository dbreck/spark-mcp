# Recaptcha & Anti-Spam

The battle against spam registrants is ongoing and must adapt as spambots become more sophisticated, but Spark has taken measures to protect our users from invalid registrations.

## Built-in Anti-Spam Protection

Each of our forms include a basic javascript validation – there is a field named "are_you_simulated" that is hidden on page load and must be left blank. As many spambots blindly complete all fields, this is enough to filter out most of the culprits.

## Recaptcha V3 Support

We also recommend using additional anti-spam measures on web forms to help protect your database; for this reason, Spark supports **Recaptcha V3**. Recaptcha is an optional security feature that can be used prior to sending registrants to Spark (if you are using an API implementation to send contacts) or within your registration form settings if you use the custom registration form code (see more in our [Registration Form Developer Guide](https://knowledge.spark.re/registration-form-developer-guide)).

## Important Limitations

**Note:** We do not currently have an integration for Spark-hosted and Iframe forms, so it is important that you do not require Recaptcha in the settings for these types of format. If you do, form submissions will not post successfully. Similarly, if your custom form does not contain a Recaptcha widget, submissions will not post successfully if Recaptcha is required in the form's settings. You should always test your forms after making any adjustments to their settings.

## Implementation for Custom Forms

If you have opted to use a custom form for your project, talk to your web developer about implementing Recaptcha and adding a widget to the custom form to block any suspicious registrations. Recaptcha has a Developer Guide with detailed instructions on how to implement this feature; the only things needed on Spark are the **Site Key** and the **Secret Key** that your developer will receive when they register for the Recaptcha API.

## Setting up Recaptcha in Spark

To save your Site Key and Secret Key to Spark:

1. Go to **Menu → Forms → List**
2. Click the **Recaptcha Setup** button
3. Enter the keys in their respective fields
4. Adjust the tolerance threshold if needed

Each registration request is scored from **0.0** (very likely to be a bot) to **1.0** (very likely a good interaction), and any request not exceeding the threshold will be rejected. 

- If you find you are still receiving spam registrants, you could **raise** the tolerance threshold
- If legitimate registrants are being rejected, you could **lower** the threshold

## Enabling Recaptcha for Forms

To use Recaptcha effectively, enable the **Require Recaptcha** setting (toggle to green) in the individual settings for the registration form you are posting to. This ensures that all registrations without a Recaptcha response are rejected.

Since Spark allows multiple registration forms, you can require Recaptcha on some forms but not others as long as the forms requiring Recaptcha contain a Recaptcha widget.

## Example Use Case

For example, while it may be beneficial to require Recaptcha on a public online registration form, if you wanted to create an email newsletter inviting a portion of your database to register for an upcoming project in their neighbourhood, you could create a separate registration form in Spark and post to that URL instead. Since you would send the registration form by email to your verified registrants, it is unlikely that this particular registration form would be targeted by spambots and Recaptcha might not be necessary.

---
*Source: https://knowledge.spark.re/anti-spam*