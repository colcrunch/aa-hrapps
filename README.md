# AA-HRAPPS
A suite of HR tools for AllianceAuth.

## Features
### Form Building & Responses
* Drag-and-Drop Form Builder
* Self-Contained Form Responses

### Administration & Management
* Streamlined Admin Frontend
* Form library allows for corps to have multiple versions of their recruitment form
  * In shared auth situations, corps can copy forms from other corps.

### Communication & Collaboration
* Threaded Comments
* Private Comments

### Integrations
* Corptools & Memberaudit
* Discord Bot Integration
  * Welcome new discord users with a prompt inviting them to talk with a recruiter.
  * Facilitate discussions between Recruiters and prospective recruits with managed discord threads for recruitment.
  * Updates to HRApps cog settings do not require a restart.

## Installation

If you are running nginx add the following to your site's nginx config. 

```
location /media/ {
    alias /var/www/myauth/media/;
}
```

Add the following to your `local.py`

```py
MEDIA_URL = "/media/"
MEDIA_ROOT = "/var/www/myauth/media/"

```

## Permissions

| Permission                         | Description                                                         |
|------------------------------------|---------------------------------------------------------------------|
| `hrappperms.access_hrapps`         | Can access the hrapps application.                                  |
| `hrappperms.access_hradmin`        | Cam access the admin frontend.                                      |
| `hrappperms.manage_hrapps`         | Full management permissions. All permission checks resolve to true. |
| `form.create_forms`                | Can create new application forms for their corp.                    |
| `form.manage_corp_forms`           | Can manage forms owned by their corp.                               |
| `forms.manage_all_forms`           | Can manage all forms regardless of corporation ownership.           |
| `formresponse.claim_recruiter`     | Can claim a response as the recruiter.                              | 
| `formresponse.claim_reviewer`      | Can claim a response as the reviewer.                               |
| `formresponse.create_response`     | Can respond to forms. (apply to corps)                              |
| `formresponse.modify_status`       | Can change the status of a response (application)                   |
| `formresponse.view_all_responses`  | Can view all responses regardless of form/corp.                     |
| `formresponse.view_corp_responses` | Can view responses to corp forms.                                   |
| `responsecomment.create_comment`   | Can comment on responses. (includes implicit view permissions)      |
| `responsecomment.view_comment`     | Can view comments on form responses                                 |