

import re



def str_center(s, width, filler=' ', extraOnRight=True, trim=True):
   selfSize = len(s)
   if width <= selfSize: 
      return s
   totalDelta = width - selfSize
   fillSize = len(filler)
   if fillSize is 1:
      if extraOnRight or (totalDelta & 1) is 0:
         return s.center(width, filler)
      else:
         return filler + s.center(width-1, filler)
   # At this point fillSize is at least 2
   copiesOfFillerNeeded = totalDelta // fillSize
   fillPerSide = totalDelta // 2
   copiesPerSide = fillPerSide // fillSize
   residual = totalDelta - (2 * copiesPerSide * fillSize)
   if trim: # use copiesPerSide of the filler and some part of filler before and after
      meanresidual = residual//2
      if residual%2 is 0:
         largerResidual = smallerResidual = meanresidual
      else:
         largerResidual = meanresidual + 1
         smallerResidual = meanresidual
      if extraOnRight:
         leftResidual, rightResidual = (smallerResidual, largerResidual)
      else:
         leftResidual, rightResidual = (largerResidual, smallerResidual)
      copies = filler*copiesPerSide
      prefix = copies + filler[0 : leftResidual]
      suffix = copies + filler[0: rightResidual]
      return prefix + s + suffix
   else: # use one more copy of filler on the chosen side
      if residual < fillSize:
         leftcount = rightcount = copiesPerSide
      else:
         if extraOnRight:
            (leftcount, rightcount) = (copiesPerSide, copiesPerSide+1)
         else:
            (leftcount, rightcount) = (copiesPerSide+1, copiesPerSide)
      prefix = leftcount * filler
      suffix = rightcount * filler
      return prefix + s + suffix

 
def str_expandtabs(s, tabs=8, strict=False):
   if s.find('\t') < 0: return s
   elif type(tabs) == int: return s.expandtabs(tabs)

   # the new code starts here: limited set of possibly uneven tabs
   answer = ''
   lastTab = tabs[-1]
   for line in s.splitlines(keepends=True):
      column = 0 ;  stop = 0;  tabposition = tabs[0] # beginning of line, first tab stop
      tabsInLine = []
      for n in range(0, len(line)):
         if line[n] == '\t': tabsInLine.append(n)
      if len(tabsInLine) == 0: answer += line
      else:
         #print("tabs in line {1} at {0}".format(tabsInLine, line))
         lastTabInLine = tabsInLine[-1]
         expanded = ''
         start = 0
         for tabx in tabsInLine:
            #print("start={0}, tabx={1}".format(start, tabx))
            expanded += line[start : tabx] # copy up to the tab in line
            column = len(expanded)
            if column > lastTab:
               if strict: 
                  raise Exception("Tab too late: column="+column+", last tab="+lastTab)
               else: start = tabx         # leave the tab there: who knows what the caller wanted?
            else:
               start = tabx+1             # next segment start immediately after the tab
               for stop in tabs:          # find the first tab beyond the current length
                  #print("   stop={0}, column={1}".format(stop, column))
                  if stop > column:       # add spaces until the expanded length is at the stop
                     while stop > column:
                        expanded += ' '; column += 1
                     break
         answer += expanded + line[lastTabInLine+1:]
   return answer


def str_findlast(s, whatToLookFor):
   lengthOfMatch = len(whatToLookFor)
   n = len(s)-lengthOfMatch
   firstToMatch = whatToLookFor[0]
   ##########################################################################################
   #
   # Suppose that firstToMatch is 'x', and we match 'x' at n in s.  If all of whatToLookFor
   # is not matched there, how much further back in `s` do we have to go to have any hope of
   # match?  If 'x' occurs later in `whatToLookFor`, we have to go back far enough so that the
   # first occurrence of 'x' after the initial one lands on the spot matching that initial one
   # now.  In particular, if 'x' occurs only at the start of whatToLookFor, we have to go
   # back at least the length of whatToLookFor before we have any hope of a match.  That is
   # the logic here in computing minBack in the next two lines of code.  In the call there
   # to "find", the second argument, "1", is the first index to look at. The effect is to find
   # the second occurrence of firstToMatch in whatToLookFor, if there is one.
   #
   ##########################################################################################
   minBack = whatToLookFor.find(firstToMatch, 1)
   if minBack < 0: minBack = lengthOfMatch
   while(n>=0):
      #print("n={0}, s[n]={1}, find index={2}".format(n, s[n], s.find(whatToLookFor, n)))
      if s[n] != firstToMatch: n -= 1
      else:
         if s.find(whatToLookFor, n)==n: return n
         else: n -= minBack
   return -1


def str_islower(s, like_python=False):
   if like_python:
      return s.islower()
   for c in s:
      if c.lower() != c: return False
   return True

def str_istitle(s):
   return str_title(s) == s # uses my title()

def str_isupper(s, like_python=False):
   if like_python:
      return s.isupper()
   for c in s:   # use MY default
      if c.upper() != c: return False
   return True


def str_reverse(s):
   asList = list(s)
   asList.reverse() # does the reversal in place: no return value
   return ''.join(asList)


_QMRE = re.compile('([\u0022\u0027\u00ab\u00bb\u2018-\u201f])') # quotation marks regular expression
def str_title(s):
   if _QMRE.search(s) is None:
      return re.sub(r"\S+", lambda mo: mo.group(0)[0].upper() + mo.group(0)[1:].lower(), s)
   else:
      parts = [part for part in _QMRE.split()]
      for k in range(0, len(parts), 4):   # unquoted, ", quoted, ", next unquoted ... 
         parts[k] = parts[k].title()
      return ''.join(parts)

