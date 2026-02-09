I'm a digital producer for Lifeline Australia. I need to populate metadata fields for a number of fields including:

Audience
Feelings
Website Section
Interest Group
Experiences
Wellbeing Stage
Topics
Quiz Question 1 	
Quiz Question 2 	
Quiz Priority

On over 150 support toolkit pages on the Lifeline site, using metadata from our old Sanity site.

## My situation

Due to things out of my control, despite being an Admin on lifeline.org.au, I don't have shell access via Drush or any control over the codebase.

My only access is via the UI and read access to the codebase.

I'm hoping to speed up this process by injecting JS into the browser. We'll need to start slowly so I can make sure it's being done right, with the hope of speeding things up eventually.

We'll also need to test it out in our UAT site once or twice before doing it on prod.

You should have access to the "browser tab" tool in Cursor, (have tested successfully today) so if you don't, let me know. I'll log us into Drupal.

## Other context

paths.csv matches the old Sanity URL to the new Drupal url.

The config of the Drupal site can be found here including content types, fields, and taxonomies:/home/aido/projects/lla-website/config/sync

Location of Sanity export is here, which just has metadata and no article contents I think: /home/aido/projects/lla-website/sanity

UAT needs http creds. UAT_USER and UAT_PASS are in .env but FYI there are "+" and "=" characters in it.

## Sanity tags

These are all the tag options in Sanity currently:

**Topics**
- Eating and body image
- Relationships
- Panic attacks
- Natural disasters
- Stress
- Self-harm
- Suicide
- Psychosis
- Grief
- Gambling
- Domestic and family violence
- Financial stress
- Trauma
- Loneliness
- Depression
- Substance Misuse
- Anxiety

**Listen, watch, or read**
- Read
- Watch
- Listen

**For others content**
- Carer Stories
- For Others Page
- Friends Family

**Quiz - Manage Now or Help Long Term**
- Long-term help
- Short-term help

**Help right now or long term**
- Long term
- Right now

**Content Type**
- Technique or Strategy
- Support Service
- Support Guide
- Real Story
- Tool or App

**Type**
- Online Program
- Book
- Website
- App

**Quiz - Something Else**
- Other topics

**Cost**
- Low cost
- Free

**Access Options**
- Online
- Phone
- Counselling
- Text
- Forum
- Peer Support
- Crisis

**State**
- National
- NT
- ACT
- SA
- TAS
- VIC
- WA
- QLD
- NSW

**Media Type**
- Audio
- Graphic
- Video

**Priority**
- Priority 3
- Priority 2
- Priority 1

**Quiz - Understanding**
- Understanding