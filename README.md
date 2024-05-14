# crate-dig
## Getting Started
Download the latest release from the [releases page](https://github.com/jake-drysdale/crate-dig/releases), unzip the folder and run the executable.

## Usage
- Pick a folder with your audio library in it, this could be something like a folder you keep all your sample packs in or a folder where you download all your tracks and albums to. 
- Then click analyze and the tool will extract information about your tracks and store them in a db (UserLibrary/embeddings/embeddings.npy)
- Once the analysis is complete you can search for a track by typing in the search bar and clicking search. The tool will then find the most similar tracks to the one you searched for and display them in the UI and save a playlist file in the UserLibrary/playlists folder.

## Updating

Updates tagged as "drop-in" will be able to be extracted over the top of the existing installation and would be very lightweight (~40MB), these will be the executables only and would not include the _internal folder. Each release will have a drop-in update available.

Updates tagged as "full" will require the user to delete the existing installation and extract the new version.

## Building
Pull the repository and run `pyinstaller cratedigAI.spec` in the root directory of the project. This will create a dist folder with the executable and _internal folder that has the modules needed to run the executable.

Alternatively you can run `pyinstaller cratedigAI_exec.spec` to create a one file executable vs the one folder executable, one file executables are larger, easier to distribute but take longer to start up.

