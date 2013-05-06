Starting Zope/Plone
===================
Before you start Plone, you should review the settings in:
 
  /home/projects/OIS/oisonline/dev/buildout.cfg
 
Adjust the ports Plone uses before starting the site, if necessary,
and run /home/projects/OIS/oisonline/dev/bin/buildout
to apply settings.
 
To start Plone, issue the following command in a terminal window:
 
   /home/projects/OIS/oisonline/dev/bin/plonectl start
 
To stop Plone, issue the following command in a terminal window:
 
   /home/projects/OIS/oisonline/dev/bin/plonectl stop


Quick operating instructions
============================
After starting, you should be able to view the Zope Management Interface at::

    http://localhost:8081/manage

And, your new Plone at::

    http://localhost:8081/Plone


Updating After Installation
===========================
Always back up your installation before customizing or updating.

Customizing the installation
----------------------------
You may control most aspects of your installation, including
changing ports and adding new packages and products by editing the
buildout.cfg file in your instance home at /home/projects/OIS/oisonline/dev.

See Martin Aspelli's excellent tutorial
"Managing projects with zc.buildout":http://plone.org/documentation/tutorial/buildout
for information on buildout options.

Apply settings by running bin/buildout in your instance directory.

Updating the installation
-------------------------
To update your installation, backup and run:

bin/buildout -n

from your instance directory. This will bring your installation up-to-date,
possibly updating Zope, Plone, eggs, and product packages in the process.
(The "-n" flag tells buildout to search for newer components.)

Check portal_migration in the ZMI after update to perform version migration
if necessary. You may also need to visit the product installer to update
product versions.

