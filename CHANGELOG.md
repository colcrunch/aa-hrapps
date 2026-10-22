# Changelog

## 1.0.4 - 2026-10-22
### Changes
* Added a warning to the discord recruitment settings card if `aadiscordbot.cogs.recruit_me` is enabled.
### Fixes
* Fixed a UI issue where recruiter role and recruit role were showing the same data. (Did not affect data saved to DB)
* Fixed a typo in the hrapps menu hook causing it not to render for users with the correct permission.
* Fixed a bug where the Welcome feature enable flag was not being honored by the cog.
* Fixed a bug where the Welcome feature was not ignoring new users who were members of an ignored state.

## 1.0.3 - 2026-09-16
### Fixes
* Fixed issue where some versions of redis caused the discord bot cog to fail to load.

## 1.0.2 - 2026-08-21
### Changes
* Added an Admin Attachments section to the admin application view page.
* Added permissions related to viewing and uploading admin attachments.
### Fixes
* Users can no longer create an application for a corp they are already a member of.

## 1.0.1 - 2026 - 08 - 13
_This release contains no code changes. It exists purely to update PyPi project information._

## 1.0.0 - 2026 - 08 - 13
> 🎉 First Release!