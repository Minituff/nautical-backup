Nautical does not provide connectivity to remote services such as S3, B2, or Google Drive. We believe there are better tools for these jobs and think it is best not to recreate them.

Here is a list of a few of our favorite solutions:

* https://kopia.io
* https://borgbackup.org
* https://restic.net
* https://duplicacy.com
* https://duplicati.com

Ideally, you would configure Nautical to create a backup at a `destination` folder, then point that folder to a remote backup solution.