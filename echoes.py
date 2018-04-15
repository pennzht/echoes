################################################
#    Echoes: Look up a word by its pronunciation alone
#    Copyright (C) 2018 pennzht
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
################################################


dictionary = 'cmudict-master/cmudict.dict'

import time
import sys
import json
import random

class Word:
    def __init__(self, spell, pron):
        self.spell = spell
        self.pronna = ptons(pron)
    def __str__(self):
        return self.spell + ' [' + ' '.join(ntops(self.pronna)) + ']'

class Tree:
    ''' Tree ::= Tree (Word, [Tree, ...])
    '''
    def __init__(self, root):
        self.root = root
        self.children = dict()
    def haschildatrank(self, rank):
        return rank in self.children
    def childatrank(self, rank):
        return self.children[rank]
    def addword(self, word):
        mydist = distance(self.root.pronna, word.pronna)
        if mydist in self.children:
            self.children[mydist].addword(word)
        else:
            self.children[mydist] = Tree(word)

def wordtojson(word):
    return ['w', word.spell, [ntop(n) for n in word.pronna]]

def jsontoword(triple):
    return Word(triple[1], triple[2])

def treetojson(tree):
    jsonchildren = dict()
    for rank in tree.children:
        jsonchildren[rank] = treetojson(tree.childatrank(rank))
    return ['t', wordtojson(tree.root), jsonchildren]

def jsontotree(pair):
    treechildren = dict()
    jsonchildren = pair[2]
    for rank in jsonchildren:
        treechildren[int(rank)] = jsontotree(jsonchildren[rank])
    parsedtree = Tree(jsontoword(pair[1]))
    parsedtree.children = treechildren
    return parsedtree

def establishencoding():
    global NTOP
    global PTON
    global PHONECOUNT
    NTOP = []
    PTON = dict()
    phonelist = ["", "M", "B", "P", "N", "D", "T", "NG", "G", "K", "DH", "TH", "ZH", "SH", "Z", "S", "V", "F", "L", "R", "W", "Y", "HH", "AH", "IH", "UH", "AA", "AO", "AE", "EH", "ER", "EY", "IY", "UW", "AW", "AY", "OW", "OY", "AH1", "IH1", "UH1", "AA1", "AO1", "AE1", "EH1", "ER1", "EY1", "IY1", "UW1", "AW1", "AY1", "OW1", "OY1"]
    for n, p in enumerate (phonelist):
        NTOP.append(p)
        PTON[p] = n
    PHONECOUNT = len(NTOP)
    NTOP.append("?")

def ntops(ns):
    return [ntop(n) for n in ns]

def ntop(n):
    return NTOP[n]

def ptons(ps):
    ans = []
    for p in ps:
        p = p.upper()
        if p == "CH":
            ans.append(pton("T")); ans.append(pton("SH"))
        elif p == "JH":
            ans.append(pton("D")); ans.append(pton("ZH"))
        else:
            ans.append(pton(p))
    return ans

def pton(p):
    p = p.upper()
    if p != '' and '0' <= p[-1] <= '9':
        if p[-1] == '0':
            p = p[:-1]
        else:
            p = p[:-1] + '1'
    # next, find p in PTON
    if p in PTON:
        return PTON[p]
    else:
        return PHONECOUNT

def d(x, y):
    ''' Measures the distance between two sounds. '''
    return D[x][y]
    
def distance(A, B):
    try:
        m = [[],[]]
        a = len(A)
        b = len(B)
        for i in range(a+1):
            m[i&1] = []
            for j in range(b+1):
                if i == 0:
                    if j == 0:
                        m[i&1].append(0)
                    else:
                        m[i&1].append(m[i&1][j-1] + d(0, B[j-1]))
                else:
                    if j == 0:
                        m[i&1].append(m[(i-1)&1][j] + d(A[i-1], 0))
                    else:
                        m[i&1].append(min(
                            m[i&1][j-1] + d(0, B[j-1]),
                            m[(i-1)&1][j] + d(A[i-1], 0),
                            m[(i-1)&1][j-1] + d(A[i-1], B[j-1])))
    except IndexError:
        print('IndexError at {} compared to {}'.format(A, B))
        raise IndexError
    return m[a&1][b]

def seekergenie(tree, mypron, tolerance):
    rootdistance = distance(tree.root.pronna, mypron)
    if rootdistance == tolerance:
        yield tree.root
    for rank in range(rootdistance-tolerance, rootdistance+tolerance+1):
        if tree.haschildatrank(rank):
            for ans in seekergenie(tree.childatrank(rank), mypron, tolerance):
                yield ans

def lookupgenie(mypron):
    '''A generator generating best matches'''
    tolerance = 0
    while True:
        seeker = seekergenie(tree, mypron, tolerance)
        for ans in seeker:
            yield ans
        tolerance += 1

def lookupbest(mypron, n):
    try:
        genie = lookupgenie(mypron)
        candidates = []
        starttime = time.time()
        for i in range(n):
            try:
                word = next(genie)
                print('  {} | {}' . format(distance(word.pronna, mypron), word))
            except StopIteration:
                break
        stoptime = time.time()
        print ('{t} seconds'.format(t=stoptime-starttime))
        print ()
    except (KeyboardInterrupt, EOFError):
        print ('Lookup aborted.')

def loaddistances(filelocation):
    f = open(filelocation)
    global D
    D = json.load(f)
    f.close()

def main():
    print('''    Echoes Copyright (C) 2018 pennzht
    This program comes with ABSOLUTELY NO WARRANTY; for details type `?w'.
    This is free software, and you are welcome to redistribute it
    under certain conditions; type `?c' for details.

    Pronunciation data provided by Carnegie Mellon University
    whose license which can be found at ./LICENSE-FOR-PRONUNCIATION-DATA

    Type the pronunciation of a word using the above pronunciation key.
    For example, try `HH AH L OW1', `SH AE T OW', and `r ae t ah t uw1 iy'.
    Separate different sounds with spaces.
    Append `1' after a sound to mark as stressed syllable.
    You can also find the pronunciation key in ./HELP

    Type `?' for more help.

    Ctrl-C to exit or abort lookup.

''')
    args = sys.argv[1:]
    establishencoding()
    loaddistances("dist.json")
    f = open("tree.json")
    global tree
    tree = jsontotree(json.load(f))
    f.close()
    while(True):
        try:
            A = input('pronunciation: ')
            if '?w' in A.lower():
                print ('''  15. Disclaimer of Warranty.

  THERE IS NO WARRANTY FOR THE PROGRAM, TO THE EXTENT PERMITTED BY
APPLICABLE LAW.  EXCEPT WHEN OTHERWISE STATED IN WRITING THE COPYRIGHT
HOLDERS AND/OR OTHER PARTIES PROVIDE THE PROGRAM "AS IS" WITHOUT WARRANTY
OF ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING, BUT NOT LIMITED TO,
THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
PURPOSE.  THE ENTIRE RISK AS TO THE QUALITY AND PERFORMANCE OF THE PROGRAM
IS WITH YOU.  SHOULD THE PROGRAM PROVE DEFECTIVE, YOU ASSUME THE COST OF
ALL NECESSARY SERVICING, REPAIR OR CORRECTION.

  16. Limitation of Liability.

  IN NO EVENT UNLESS REQUIRED BY APPLICABLE LAW OR AGREED TO IN WRITING
WILL ANY COPYRIGHT HOLDER, OR ANY OTHER PARTY WHO MODIFIES AND/OR CONVEYS
THE PROGRAM AS PERMITTED ABOVE, BE LIABLE TO YOU FOR DAMAGES, INCLUDING ANY
GENERAL, SPECIAL, INCIDENTAL OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE
USE OR INABILITY TO USE THE PROGRAM (INCLUDING BUT NOT LIMITED TO LOSS OF
DATA OR DATA BEING RENDERED INACCURATE OR LOSSES SUSTAINED BY YOU OR THIRD
PARTIES OR A FAILURE OF THE PROGRAM TO OPERATE WITH ANY OTHER PROGRAMS),
EVEN IF SUCH HOLDER OR OTHER PARTY HAS BEEN ADVISED OF THE POSSIBILITY OF
SUCH DAMAGES.

  17. Interpretation of Sections 15 and 16.

  If the disclaimer of warranty and limitation of liability provided
above cannot be given local legal effect according to their terms,
reviewing courts shall apply local law that most closely approximates
an absolute waiver of all civil liability in connection with the
Program, unless a warranty or assumption of liability accompanies a
copy of the Program in return for a fee.

''')
            elif '?c' in A.lower():
                print ('''  0. Definitions.

  "This License" refers to version 3 of the GNU General Public License.

  "Copyright" also means copyright-like laws that apply to other kinds of
works, such as semiconductor masks.

  "The Program" refers to any copyrightable work licensed under this
License.  Each licensee is addressed as "you".  "Licensees" and
"recipients" may be individuals or organizations.

  To "modify" a work means to copy from or adapt all or part of the work
in a fashion requiring copyright permission, other than the making of an
exact copy.  The resulting work is called a "modified version" of the
earlier work or a work "based on" the earlier work.

  A "covered work" means either the unmodified Program or a work based
on the Program.

  To "propagate" a work means to do anything with it that, without
permission, would make you directly or secondarily liable for
infringement under applicable copyright law, except executing it on a
computer or modifying a private copy.  Propagation includes copying,
distribution (with or without modification), making available to the
public, and in some countries other activities as well.

  To "convey" a work means any kind of propagation that enables other
parties to make or receive copies.  Mere interaction with a user through
a computer network, with no transfer of a copy, is not conveying.

  An interactive user interface displays "Appropriate Legal Notices"
to the extent that it includes a convenient and prominently visible
feature that (1) displays an appropriate copyright notice, and (2)
tells the user that there is no warranty for the work (except to the
extent that warranties are provided), that licensees may convey the
work under this License, and how to view a copy of this License.  If
the interface presents a list of user commands or options, such as a
menu, a prominent item in the list meets this criterion.

  1. Source Code.

  The "source code" for a work means the preferred form of the work
for making modifications to it.  "Object code" means any non-source
form of a work.

  A "Standard Interface" means an interface that either is an official
standard defined by a recognized standards body, or, in the case of
interfaces specified for a particular programming language, one that
is widely used among developers working in that language.

  The "System Libraries" of an executable work include anything, other
than the work as a whole, that (a) is included in the normal form of
packaging a Major Component, but which is not part of that Major
Component, and (b) serves only to enable use of the work with that
Major Component, or to implement a Standard Interface for which an
implementation is available to the public in source code form.  A
"Major Component", in this context, means a major essential component
(kernel, window system, and so on) of the specific operating system
(if any) on which the executable work runs, or a compiler used to
produce the work, or an object code interpreter used to run it.

  The "Corresponding Source" for a work in object code form means all
the source code needed to generate, install, and (for an executable
work) run the object code and to modify the work, including scripts to
control those activities.  However, it does not include the work's
System Libraries, or general-purpose tools or generally available free
programs which are used unmodified in performing those activities but
which are not part of the work.  For example, Corresponding Source
includes interface definition files associated with source files for
the work, and the source code for shared libraries and dynamically
linked subprograms that the work is specifically designed to require,
such as by intimate data communication or control flow between those
subprograms and other parts of the work.

  The Corresponding Source need not include anything that users
can regenerate automatically from other parts of the Corresponding
Source.

  The Corresponding Source for a work in source code form is that
same work.

  2. Basic Permissions.

  All rights granted under this License are granted for the term of
copyright on the Program, and are irrevocable provided the stated
conditions are met.  This License explicitly affirms your unlimited
permission to run the unmodified Program.  The output from running a
covered work is covered by this License only if the output, given its
content, constitutes a covered work.  This License acknowledges your
rights of fair use or other equivalent, as provided by copyright law.

  You may make, run and propagate covered works that you do not
convey, without conditions so long as your license otherwise remains
in force.  You may convey covered works to others for the sole purpose
of having them make modifications exclusively for you, or provide you
with facilities for running those works, provided that you comply with
the terms of this License in conveying all material for which you do
not control copyright.  Those thus making or running the covered works
for you must do so exclusively on your behalf, under your direction
and control, on terms that prohibit them from making any copies of
your copyrighted material outside their relationship with you.

  Conveying under any other circumstances is permitted solely under
the conditions stated below.  Sublicensing is not allowed; section 10
makes it unnecessary.

  3. Protecting Users' Legal Rights From Anti-Circumvention Law.

  No covered work shall be deemed part of an effective technological
measure under any applicable law fulfilling obligations under article
11 of the WIPO copyright treaty adopted on 20 December 1996, or
similar laws prohibiting or restricting circumvention of such
measures.

  When you convey a covered work, you waive any legal power to forbid
circumvention of technological measures to the extent such circumvention
is effected by exercising rights under this License with respect to
the covered work, and you disclaim any intention to limit operation or
modification of the work as a means of enforcing, against the work's
users, your or third parties' legal rights to forbid circumvention of
technological measures.

  4. Conveying Verbatim Copies.

  You may convey verbatim copies of the Program's source code as you
receive it, in any medium, provided that you conspicuously and
appropriately publish on each copy an appropriate copyright notice;
keep intact all notices stating that this License and any
non-permissive terms added in accord with section 7 apply to the code;
keep intact all notices of the absence of any warranty; and give all
recipients a copy of this License along with the Program.

  You may charge any price or no price for each copy that you convey,
and you may offer support or warranty protection for a fee.

  5. Conveying Modified Source Versions.

  You may convey a work based on the Program, or the modifications to
produce it from the Program, in the form of source code under the
terms of section 4, provided that you also meet all of these conditions:

    a) The work must carry prominent notices stating that you modified
    it, and giving a relevant date.

    b) The work must carry prominent notices stating that it is
    released under this License and any conditions added under section
    7.  This requirement modifies the requirement in section 4 to
    "keep intact all notices".

    c) You must license the entire work, as a whole, under this
    License to anyone who comes into possession of a copy.  This
    License will therefore apply, along with any applicable section 7
    additional terms, to the whole of the work, and all its parts,
    regardless of how they are packaged.  This License gives no
    permission to license the work in any other way, but it does not
    invalidate such permission if you have separately received it.

    d) If the work has interactive user interfaces, each must display
    Appropriate Legal Notices; however, if the Program has interactive
    interfaces that do not display Appropriate Legal Notices, your
    work need not make them do so.

  A compilation of a covered work with other separate and independent
works, which are not by their nature extensions of the covered work,
and which are not combined with it such as to form a larger program,
in or on a volume of a storage or distribution medium, is called an
"aggregate" if the compilation and its resulting copyright are not
used to limit the access or legal rights of the compilation's users
beyond what the individual works permit.  Inclusion of a covered work
in an aggregate does not cause this License to apply to the other
parts of the aggregate.

  6. Conveying Non-Source Forms.

  You may convey a covered work in object code form under the terms
of sections 4 and 5, provided that you also convey the
machine-readable Corresponding Source under the terms of this License,
in one of these ways:

    a) Convey the object code in, or embodied in, a physical product
    (including a physical distribution medium), accompanied by the
    Corresponding Source fixed on a durable physical medium
    customarily used for software interchange.

    b) Convey the object code in, or embodied in, a physical product
    (including a physical distribution medium), accompanied by a
    written offer, valid for at least three years and valid for as
    long as you offer spare parts or customer support for that product
    model, to give anyone who possesses the object code either (1) a
    copy of the Corresponding Source for all the software in the
    product that is covered by this License, on a durable physical
    medium customarily used for software interchange, for a price no
    more than your reasonable cost of physically performing this
    conveying of source, or (2) access to copy the
    Corresponding Source from a network server at no charge.

    c) Convey individual copies of the object code with a copy of the
    written offer to provide the Corresponding Source.  This
    alternative is allowed only occasionally and noncommercially, and
    only if you received the object code with such an offer, in accord
    with subsection 6b.

    d) Convey the object code by offering access from a designated
    place (gratis or for a charge), and offer equivalent access to the
    Corresponding Source in the same way through the same place at no
    further charge.  You need not require recipients to copy the
    Corresponding Source along with the object code.  If the place to
    copy the object code is a network server, the Corresponding Source
    may be on a different server (operated by you or a third party)
    that supports equivalent copying facilities, provided you maintain
    clear directions next to the object code saying where to find the
    Corresponding Source.  Regardless of what server hosts the
    Corresponding Source, you remain obligated to ensure that it is
    available for as long as needed to satisfy these requirements.

    e) Convey the object code using peer-to-peer transmission, provided
    you inform other peers where the object code and Corresponding
    Source of the work are being offered to the general public at no
    charge under subsection 6d.

  A separable portion of the object code, whose source code is excluded
from the Corresponding Source as a System Library, need not be
included in conveying the object code work.

  A "User Product" is either (1) a "consumer product", which means any
tangible personal property which is normally used for personal, family,
or household purposes, or (2) anything designed or sold for incorporation
into a dwelling.  In determining whether a product is a consumer product,
doubtful cases shall be resolved in favor of coverage.  For a particular
product received by a particular user, "normally used" refers to a
typical or common use of that class of product, regardless of the status
of the particular user or of the way in which the particular user
actually uses, or expects or is expected to use, the product.  A product
is a consumer product regardless of whether the product has substantial
commercial, industrial or non-consumer uses, unless such uses represent
the only significant mode of use of the product.

  "Installation Information" for a User Product means any methods,
procedures, authorization keys, or other information required to install
and execute modified versions of a covered work in that User Product from
a modified version of its Corresponding Source.  The information must
suffice to ensure that the continued functioning of the modified object
code is in no case prevented or interfered with solely because
modification has been made.

  If you convey an object code work under this section in, or with, or
specifically for use in, a User Product, and the conveying occurs as
part of a transaction in which the right of possession and use of the
User Product is transferred to the recipient in perpetuity or for a
fixed term (regardless of how the transaction is characterized), the
Corresponding Source conveyed under this section must be accompanied
by the Installation Information.  But this requirement does not apply
if neither you nor any third party retains the ability to install
modified object code on the User Product (for example, the work has
been installed in ROM).

  The requirement to provide Installation Information does not include a
requirement to continue to provide support service, warranty, or updates
for a work that has been modified or installed by the recipient, or for
the User Product in which it has been modified or installed.  Access to a
network may be denied when the modification itself materially and
adversely affects the operation of the network or violates the rules and
protocols for communication across the network.

  Corresponding Source conveyed, and Installation Information provided,
in accord with this section must be in a format that is publicly
documented (and with an implementation available to the public in
source code form), and must require no special password or key for
unpacking, reading or copying.

''')
            elif '?' in A:
                print ('''        Phoneme Example Translation
        ------- ------- -----------
        AA	odd     AA D
        AE	at	AE T
        AH	hut	HH AH T
        AO	ought	AO T
        AW	cow	K AW
        AY	hide	HH AY D
        B 	be	B IY
        CH	cheese	CH IY Z
        D 	dee	D IY
        DH	thee	DH IY
        EH	Ed	EH D
        ER	hurt	HH ER T
        EY	ate	EY T
        F 	fee	F IY
        G 	green	G R IY N
        HH	he	HH IY
        IH	it	IH T
        IY	eat	IY T
        JH	gee	JH IY
        K 	key	K IY
        L 	lee	L IY
        M 	me	M IY
        N 	knee	N IY
        NG	ping	P IH NG
        OW	oat	OW T
        OY	toy	T OY
        P 	pee	P IY
        R 	read	R IY D
        S 	sea	S IY
        SH	she	SH IY
        T 	tea	T IY
        TH	theta	TH EY T AH
        UH	hood	HH UH D
        UW	two	T UW
        V 	vee	V IY
        W 	we	W IY
        Y 	yield	Y IY L D
        Z 	zee	Z IY
        ZH	seizure	S IY ZH ER

Type the pronunciation of a word using the above pronunciation key. \nFor example, try `HH AH L OW1', `SH AE T OW', and `r ae t ah t uw1 iy'. \nSeparate different sounds with spaces. \nAppend `1' after a sound to mark as stressed syllable. \nYou can also find the pronunciation key in ./HELP\n\n ''')
            else:
                mypron = ptons(A.split())
                lookupbest(mypron, 10)
        except (KeyboardInterrupt, EOFError):
            break

main()

