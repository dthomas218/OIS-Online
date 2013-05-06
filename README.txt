Installing
==========

Clone the github repo::

   $ git clone https://github.com/dthomas218/OIS-Online /the/server/directory
   $ cd /the/server/directory
   
Create a buildout.cfg that look like this:

   [buildout]
   extends=production.cfg
   
Or "development.cfg" if this is for development, or "staging.cfg" if it is a
staging server. The main differences between production adn staging is the 
ports. If you need other ports that the ones stated you can override them in
the local buildout.cfg (which should never be checked into git).

Run the buildout::

    python2.7 bootstrap.py --distribute
    bin/buildout
    
Go for a coffee. Make sure the buildout worked properly by looking at the
output. It should also have a section of picked versions at the end::

   *************** PICKED VERSIONS ****************
   [versions]
   
   *************** /PICKED VERSIONS ***************

This section should be empty, with the possible exceptions of Security HotFixes.


Starting Zope/Plone
===================
 
To start Plone in a production or staging environmeny, issue the following
command in a terminal window::
 
   bin/supervisord
   
This will start all Plone instances, the ZODB server, a haproxy load balancer
and a varnish cache. You stop all services with:

   bin/supervisorctl shutdown

In a development environment, use

   bin/instance fg
   
There is no load balancer or cache, and no separate ZODB server. You stop the
instance with the shutdown button in the ZMI, or by pressing Ctrl-C in the
terminal.


Quick operating instructions
============================
After starting, you should be able to view the Zope Management Interface at::

    http://localhost:<port>/manage

Where port in 8080 in development, 8081 in production and 9081 for staging.
8080 and 9080 are also used in production and staging but that's for the
varnish cache, so it's the "end" port, the one the Apache server connects to.


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

