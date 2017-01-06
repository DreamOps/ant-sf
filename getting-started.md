# Getting Started - DRAFT

Most people will already have Salesforce project in progress. Here is a 
step-by-step from the beginning, and you can skip any steps that are 
already done. 

(1) Provision a Salesforce org for your work. 
* For direct customer projects, this environment will be your business org, 
usually an Enterprise Edition environment with sandboxes. 
* For partners building AppExchange packages, this org will be a Developer 
Edition org, provisioned from your Environonment Hub. You will also want to 
provision a Trialforce Source org.

(2) Choose a host for your source code repository, both Bitbucket and 
GitHub are already supported. 

(3) Fork the ant-dx repo in Bitbucket or GitHub (we sync to both).
* If you implement the *.example files, modify the .gitignore on your fork

(4a) Direct Setup - Inhouse developers and consultants
* Provision a develop sandbox. 
* In the develop sandbox, create a unmanaged package, also named develop. 
* If you've started any customization work in production, add the 
components to the develop package. 

(4b) Product Setup - AppExchange Developers and ISVs
* Choose a namespace for your managed package, along with a full name. 
** The namespace is used as an code-level identifier to uniquely 
distinguish your AppExchange packages from all other packages. 
** In your AppExchange listing, the longer "full name" is shown. 
* In you Developer Edition org, create a package and register your namespace.
* If you've started any development work in the DE org, add the components 
to your package. 

(5) The initial setup needs to done locally. Other tasks can be run from 
Bamboo, Jenkins, or TeamCity.
* Checkout your ant-dx fork.
* Create an empty repository in Bitbucket or Github for the Salesforce 
metadata. 
* Clone it to a local folder that shares the same parent folder with the 
ant-dx fork, so that the folders are side-by-side.
* Change to the root folder of the new repository, and run 
"git init".

Direct Setup

(6a) Initially, the master/production branch will be empty, except for the 
Git configuration files and a default package manifest. Then, from task 
sandboxes, we add components to be deployed back to production. 
* Change to the ant-dx folder, and to setup the default configuration, run 

% ant -Dhome=org_folder -Dsf_credentials=username:passwordToken InitProduction

(6b) If InitProduction succeeds, provision a "develop" sandbox (a Developer 
sandbox format is fine).

(6c) If you'll be using a build server, the server setup instructions can be 
followed now. 

(6d) Create a second task sandbox for the initial work on the org. Every task 
needs a unique ID, which ideally maps to a key in a issue tracker, like JIRA. 

(6e) Run StartNewTask from the build server or command line interface:

% ant StartNewTask -Dhome=org_folder -Dsf_credentials=username:passwordToken 

(6f) Whenever you create or modify a component in the task sandbox, add that 
component to the "develop" package in the sandbox. All of the components that 
you are creating or modifying need to be added to the develop package. 

(6g) When the task is complete, and all the touched components are added to 
the develop package, run ReadyToReview from the server or CLI:

% ant ReadyToReview -Dhome=org_folder -Dsf_credentials=username:passwordToken 

(6h) Review and merge the pull request created by ReadyToReview, and continue 
to StartNewTask sandboxes.  

(6i) At the end of the first sprint, create a pull request from develop to 
master. After the pull request is merged, run DeployToProduction.

% ant DeployToProduction -Dhome=org_folder -Dsf_credentials=username:passwordToken 

(6j) Create a staging sandbox 

----

Notes 

Big Bang
* Use builders to start in production (objects, record types, 
layouts). 
* After initial groundwork, provision staging and develop 
sandboxes, branches, and backup branches. 
* From develop sandbox, add work-in-progress into develop package. 
* Deploy develop package to develop branch. 
* Merge develop branch into staging, and staging into master. 
* Provison task sandboxes normally for ongoing work. 

Steady State
* Do not work in production. 
* Provision task sandbox and develop sandbox, with empty develop package. 
* Initialize empty master branch, checkout backup, staging, bkstaging, 
and develop. 
* Add task work into develop package normally.
* After first sprint, merge develop into staging and staging into master, 
deploy to production, and provision staging sandbox.

----

InitProduction
git clone git@github.com:TedHusted/sf-org.git
cd sf-org
git init
cd ../ant-dx
ant -Dhome=sf-org sf_credentials=admin@sf.org:PASSWORDTOKEN InitProduction

----

git checkout -b backup & git push 
git checkout -b bkstaging  & git push 
git checkout -b staging & git push 
git checkout -b develop & git push

----

Provision task sandbox
StartNewTask 

ant -Dhome=sf-org -Dsf_credentials=surveyforce@dreamops.org:******** -Dtask=ABC-123 StartNewTask

ant -Dhome=sf-org -Dsf_credentials=surveyforce@dreamops.org:=******** -Dtask=ABC-123 StartNewTask -Dsf_fullName=working

----

Develop task
Add new components to develop package. 
ReadyToReviewTask

 ant -Dhome=sf-org -Dsf_credentials=surveyforce@dreamops.org:28-Dec-2016 -Dtask=ABC-123 -Dsf_fullName=working 

 -Drepo_user=TedHusted 
 -Drepo_password=********

 -Drepo_host=github.com 
 -Drepo_owner=TedHusted 

 -Drepo_fullname=TedHusted/sf-org 

 ReadyToReviewTask

----

