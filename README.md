# sndsw

<details>
  <summary>Table of contents</summary>
  
- [sndsw](#sndsw)
* [Introduction](#introduction)
    + [Branches](#branches)
* [Build Instructions using CVMFS](#build-instructions-using-cvmfs)
* [Local build, without access to CVMFS](#local-build--without-access-to-cvmfs)
* [Run Instructions](#run-instructions)
* [Docker Instructions](#docker-instructions)
* [Contributing Code](#contributing-code)

</details>

## Introduction

If you have questions or problems, please feel free to contact @olantwin or the 
@SND-LHC/core-developers. For troubleshooting and development, we plan to discuss on [Mattermost](https://mattermost.web.cern.ch/sndlhc/channels/software).

The [snd-software](mailto:snd-software@cern.ch) mailing list can be used to discuss the software and report issues. Important annoucements will be made there.

The [snd-software-notifications](mailto:snd-software-notifications@cern.ch) mailing list will be used for automated notifications from Github and CI/CD etc..

Both mailing lists are self-subscribe CERN e-groups.

### Branches

<dl>
  <dt><code>master</code></dt>
  <dd>Main development branch.
      All python code is <b>required to be compatible with 3</b>
      Requires aliBuild default <code>release</code>.</dd>
</dl>

## Build Instructions using CVMFS

On `lxplus` or any CC7 machine with access to CVMFS, you can do the following:

``` bash
source /cvmfs/ship.cern.ch/SHiP-2021/latest/setUp.sh
$ALIBUILD/aliBuild build sndsw -c snddist --always-prefer-system
```

1. Clone the [snddist](https://github.com/SND-LHC/snddist), which containts the recipes to build `sndsw` and it's dependencies:
    ```bash
    git clone https://github.com/SND-LHC/snddist
    ```

2. Make sure you can access the SHiP CVMFS Repository
    ```bash
    ls /cvmfs/ship.cern.ch
    ```
3. Source the `setUp.sh` script
    ```bash
    source /cvmfs/ship.cern.ch/SHiP-2021/latest/setUp.sh
    ```

4. Build the software using aliBuild
    ```bash
    $ALIBUILD/aliBuild build sndsw -c snddist --always-prefer-system
    ```
5. If you need to modify `sndsw`, create a development copy
    ``` bash
    $ALIBUILD/aliBuild init -c snddist sndsw
    ```
    
For more information on using `aliBuild`, see its [documentation](https://alisw.github.io/alibuild/) (note, some things are ALICE specific and will not apply to SND@LHC software).

If you exit your shell session and you want to go back working on it, make sure to re-execute the third step.

To load the `sndsw` environment, after you build the software, you can simply use:

6. Load the environment
    ```bash
    $ALIBUILD/alienv enter sndsw/latest
    ```

However, this won't work if you are using HTCondor. In such case you can do:

```bash
eval $ALIBUILD/alienv load sndsw/latest
```

If you modify `sndsw`, simply repeat step 4 from `sndsw`'s parent directory.

## Local build, without access to CVMFS
Commands are similar to the previous case, but without access to CVMFS you need to build the required packages from source.

1. Clone the [snddist](https://github.com/SND-LHC/snddist), which containts the recipes to build `sndsw` and it's dependencies:
    ```bash
    git clone https://github.com/SND-LHC/snddist.git
    ```
    
2. Install [aliBuild](https://github.com/alisw/alibuild)
    ``` bash
    pip3 install --user alibuild
    ```
    and make sure that it is in your $PATH

2. Build the software using aliBuild
    ```bash
    aliBuild build sndsw -c snddist
    ```
    If you run into any problems, `aliDoctor` can help determine what the problem is.
3. Load the environment
    ```bash
    alienv enter sndsw/latest
    ```

## Run Instructions

**To be updated**

<!-- Set up the bulk of the environment from CVMFS. -->

<!-- ```bash -->
<!-- source /cvmfs/ship.cern.ch/SHiP-2018/latest/setUp.sh -->
<!-- ``` -->

<!-- Load your local FairShip environment. -->

<!-- ```bash -->
<!-- alibuild/alienv enter (--shellrc) FairShip/latest -->
<!-- ```     -->

<!-- Now you can for example simulate some events, run reconstruction and analysis: -->

<!-- ```bash -->
<!-- python $FAIRSHIP/macro/run_simScript.py -->
<!-- >> Macro finished succesfully. -->
<!-- >> Output file is  ship.conical.Pythia8-TGeant4.root -->

<!-- python $FAIRSHIP/macro/ShipReco.py -f ship.conical.Pythia8-TGeant4.root -g geofile_full.conical.Pythia8-TGeant4.root -->
<!-- >> finishing pyExit -->

<!-- python -i $FAIRSHIP/macro/ShipAna.py -f ship.conical.Pythia8-TGeant4_rec.root -g geofile_full.conical.Pythia8-TGeant4.root -->
<!-- >> finished making plots -->
<!-- ``` -->

<!-- Run the event display: -->

<!-- ```bash -->
<!-- python -i $FAIRSHIP/macro/eventDisplay.py -f ship.conical.Pythia8-TGeant4_rec.root -g geofile_full.conical.Pythia8-TGeant4.root -->
<!-- // use SHiP Event Display GUI -->
<!-- Use quit() or Ctrl-D (i.e. EOF) to exit -->
<!-- ``` -->

## Docker Instructions

Docker is **not** the recommended way to run `sndsw` locally. It is ideal
for reproducing reproducible, stateless environments for debugging, HTCondor
and cluster use, or when a strict separation between `sndsw` and the host is
desirable.

1. Build an docker image from the provided `Dockerfile`:
    ```bash
    git clone https://github.com/SND-LHC/sndsw.git
    cd sndsw
    docker build -t sndsw .
    ``` 
2. Run the `sndsw` docker image:
    ```bash
    docker run -i -t --rm sndsw /bin/bash
    ``` 
3. Advanced docker run options:
    ```bash
    docker run -i -t --rm \
    -e DISPLAY=unix$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v /local_workdir:/image_workdir \
    sndsw /bin/bash
    ``` 
    The option `-e DISPLAY=unix$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix` forwards graphics from the docker to your local system (similar to `ssh -X`). The option `-v /local_workdir:/image_workdir` mounts `/local_workdir` on the local system as `/image_workdir` within docker.

## Contributing Code

All packages are managed in Git and GitHub. Please either use the web interface to create pull requests or issues, or [send patches via email](https://git-send-email.io/).

If your changes would also benefit [FairShip](https://github.com/ShipSoft/FairShip), please consider making a pull-request for your changes there. We can then pick up the changes from FairShip automatically.
