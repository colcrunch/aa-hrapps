# AA-HRAPPS
A WIP Recruitment tool.

## Features
* Drag and drop form builder
* Admin frontend for easy management
* Corptools and memberaudit integration
* Doscordbot integration

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