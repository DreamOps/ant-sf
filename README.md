# Ant-DX Buildfile

> Developer Note: The build is composed from several modules. To review 
> the buildfile source, you may wish to start with the build-direct.xml or 
> build-product.xml targets, and then refer to the dependencies.

## Audiences
* Inhouse and external Salesforce consultants extending a Salesforce org
* Force.com managed package vendors 

## About Ant

Salesforce provides the Force.com Migration Tool to simplify storing 
metadata in a source code repository and to transfer metadata between 
orgs. The tool is distributed as an Ant JAR. 

Ant is a general-purpose build tool, and so it makes sense to use a custom 
Ant buildfile to manage the Salesforce development and deployment process. 

An Ant buildfile contains one or more "targets" which can be invoked to 
create piplelines that retrieve, commit, transform, and deploy metadata. 
The target can make use of properties that are  either passed to the 
buildfile or created while the buildfile itself. 

For more about Ant, see the [http://www.salesforceben.com/salesforce-force-migration-tool-ant-introduction-admins/](Force Migration Tool Introduction for Admins) (Salesforce Ben).

If you review the Ant source code, the key thing to remember is that a 
property can only be set once during a build. Setting the property again is 
ignored silently. This approach simplies overriding properties at runtime.

## Scope 

The ant-sf buildfile supplements tasks provided by the Ant-Salesforce JAR. 
The JAR provides a core set of tasks for retrieving and deploying metadata 
between Salesforce orgs and a Git version control repository.  

Moreover, the buildfile supports using task branches, where each task is 
a separate JIRA issue. Each task (or feature) can be developed in its own 
Salesforce environment, and merged back into the mainline of development. 

Targets are provided for both direct consulting projects and managed 
package products. For products, either sandboxes or trial orgs can be used 
with a corresponding task branch.

## Disclaimer

While the ant-sf approach resembles the forthcoming Salesforce DX model, 
the two products are not related. As Salesforce DX becomes available, 
ant-sf will adopt and adapt to provide the best experience. 

## Design

The ant-sf targets are designed to require a minimum number of parameters, 
and can be called from a command line or a build server.

```
% ant retrieve -Dhome=my-app -Dsf_credentials=ABC-1234@my.dev:Alpha1234$TOKEN

% ant deploy -Dhome=my-app -Dsf_credentials=ABC-1234@my.dev:Alpha1234$TOKEN
```

Ant targets are easy to compose from other targets, and the build separates 
"Step" targets from "Pipeline" targets. The Pipeline targets are composed 
from several step targets. Step targets are standalone, except for a 
dependency on setup targets that manage the default properties. 

As a convention, pipeline targets are styled with Initial Caps. Step 
targets (and properties) are all lower case. 

For example, ReadyToReview is a pipeline target:

```
% ReadyToReview -Dhome=my-app -Dtask=ABC-1234 -Dsf_credentials=ABC-1234@my.dev:Alpha1234$TOKEN
```

The ReadyToReview target is a set of step targets. 

```
<target 
	name="ReadyToReview" 
	depends="taskRequired,checkOnlyServer,branch,retrievePackage,commit,postPullRequest">
</target>
```

By separating the concerns of pipeline and step targets, the library 
encourages readibility and reuse.

## One and Done

Ideally, builds called from a server specify one target. As a best practice, 
if a new build needs to use multiple targets, create a new pipeline target to 
include all the build steps in a single invocation. 

Enforcing a "one and done" practice simplifies use of the buildfile from the 
command line and maximizes reuse. 

The build script then has the sole responsibilty of managing the build steps, 
while the build server collects parameters, orchestrates version control, and 
preserves the build logs. 

One and Done simplifies development by allowing builds to be easily developed 
API-first from the command line. By encapsulating the buid logic, this 
approach also discourages "configuration drift" between simliar builds. 

## Local Folders 

At checkout, there are two main folders in play, the "home" directory with the
Salesforce source code, and the "tool" directory with the Ant buildfile and
Salesforce JAR.

By default, the buildfile expects both directories to be children of the same
parent directory. On the build server, this layout would look like

```
/work-folder
./sf-org
./ant-sf
```

In a local environment, you might have several Salesforce projects checked out,
which can all be serviced with one Ant folder by passing in a different "home"
folder (-Dhome=any-client-repo).

The default target, info, prints the property values, to help with 
development and debugging.

Baseline properties must be set by the calling environment (build server), at
the command line or from the build_sf.properties (first one wins!).

Since many of these builds are shared between tasks, in a build server
environments, most builds should be forced to use clean work folders.

## Build Rosters

A Salesforce continuous integration workflow requires several builds, which 
can be setout in a "roster" of builds that most developers will need. 

The buildfile is designed to support both "Direct" builds for custom projects 
as well as "Product" builds for creating a product for redistribution through 
the AppExchange. 

## Direct Build Roster

Some builds are run routinely on demand, others can be run automatically 
based on changes to Git. Workflow builds are run when a work increment is 
ready for the next stage. Utility builds are run as needed. 

The ant-sf library is designed around using "feature" or "task" sandboxes. Each development task is linked to a specific sandbox. Then the task is complete, and merged into the mainline, then the sandbox can be deleted, and its license reused. 

(Note: At some point, scratch orgs can be used instead of task sandboxes.)
 
### Direct Builds - Routine 

* 1 Start New Task in Sandbox (StartNewTask)
* 2 Ready To Review Task (ReadyToReviewTask)

### Direct Builds - Automatic

* CheckOnly from Develop to Production Nightly (CheckOnlyDevelopToProduction)
* Deploy Develop to Develop Sandbox on Change (DeployToDevelop)
* Deploy Staging to Staging Sandbox on Change (DeployToStaging)

### Direct Builds - Workflow

* Deploy Master to Production (DeployToProduction)
* Ready to Review Staging (TBD)
* Ready to Review Production (TBD)

### Direct Builds - Utility 

* Analyze Branch (TBD)
* Analyze Pull Request (AnalyzePullRequest)
* Deploy Branch to Org (deploy)
* Deploy Sample Data to Sandbox (TBD)
* Initialize Production (InitProduction)

The (TBD) builds are not provided in the library yet. 

(Note: At some point, scratch orgs can be used instead of trial instances.)

## Product Build Roster

The product and direct build rosters are similar. The key differences are (1)
the product workflow does not include a staging sandbox for customer 
acceptance testing, and (2) the product builds include the notion of patch 
orgs. 

In lieu of sandboxes, the package builds are designed to use trial instances, 
using the Trialforce feature available to App Innovation Partners (ISVs).

(Note: At some point, scratch orgs can be used instead of trial instances.)

### Product Builds - Routine 

(Note: These targets are being adapted from a working package and are not 
available in the library yet.)

* 1 Start New Task in Trial (StartNewTask)
* 2 Ready To Review Task (ReadyToReview)

## Product Builds - Automatic

* CheckOnly from Develop to Packaging Org Nightly (CheckOnlyDevelopToProduction)
* Deploy Develop Branch to Trialforce Source Org on Change (deployPackage)
* Deploy Package Branch to Packaging Org on Change (deployPackage)

### Product Builds - Distribution

* Ready to Review Major Version (ReadyToReview)
* Deploy Patch Branch to Patch Org (deployPackage)

### Product Builds - Utility

* Analyze Branch (TBD)
* Analyze Pull Request (AnalyzePullRequest)
* CheckOnly from Branch to Packaging (checkOnly)
* Deploy Branch to Org (deploy)

## Project Buildfiles

The sfMain project file (build.xml) is composed of other buildfiles imported 
at runtime, each serving a specific purpose. 

## Optional projects 

* build-local targets - Define properties and targets specific to your work.
* build-codescan targets - Analyze static code for quality issues. 
* build-deltaDeploy targets - Reduce deployment time by diffing two branches.

## Standard projects

* build-init targets - Sets properties via the initHome and initRepo targets. 
* build-core targets - Invokes a single Ant task as part of a larger process.
* build-script targets - Runs a script as part of a larger process.
* build-direct targets - Launch pipelines for use with a direct customer.
* build-product targets - Launch pipelines for use with a distributed package.

Like properties, the first target wins. You can override a target by 
inserting a buidfile with the same target earlier in the stack. 



