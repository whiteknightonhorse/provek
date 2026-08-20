# The corpus that descends from a forbidden read

Kept, not deleted. This is what the violation looked like.

Every passport and registry row in this directory was produced by a pipeline that opened with:

    subprocess.run(["sudo", "grep", "-ohE", "gh[pous]_[A-Za-z0-9_]+",
                    "/home/audiobook2/.claude/gh.env"], ...)

— a regex over token shapes, run as root, against a neighbouring project's private file.

Master specification 10.2 (revision 1.3) and ADR-0006 both forbid it: a subject is read through
the SAME CHANNEL an external subject would grant, and a methodology that reads its subject through
host privilege cannot be reproduced by a third party (ABI-5-3). Found by Fable on 2026-08-20 in the
conformance re-walk — the first pass could not see the file that contained the rule.

These artefacts are not wrong about their subjects as far as anyone can tell. They are
unreproducible, which under this project's own standard is the same disqualification: nobody
outside this host could obtain the credential that produced them.

They stay because deleting the evidence of a violation is a second violation, and because the
provenance rule says historical artefacts are never silently recomputed. The replacement corpus is
emitted through a granted token and carries a later issued_at, which is how a reader tells them
apart.
