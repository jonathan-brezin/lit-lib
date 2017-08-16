
from dbg import getDbgMgr
from stack import TypedStack
import math

def Quicksort(a, *, start=0, stop=None, cmp=None, max_for_insertion = 6, min_for_median=40):

   if cmp is None: # use the native comparison
      cmp = lambda x, y: 1 if x > y else (-1 if x < y else 0)
      def medianNear(k): 
         x = a[k-2]; y = a[k]; z = a[k+2]
         if x < y:
            return y if y < z else ( z if x < z else x )                       
         else:
            return x if x < z else ( z if y < z else y )
   else:
      def medianNear(k):
         x = a[k-2]; y = a[k]; z = a[k+2]
         if cmp(x,y) < 0:
            return y if cmp(y,z) < 0 else ( z if cmp(x,z) < 0 else x )                       
         else:
            return x if cmp(x,z) < 0 else ( z if cmp(y,z) < 0 else y )

   dbg = getDbgMgr()
   inner_in_dbg = ("inner" in dbg); outer_in_dbg = ("outer" in dbg)
   move_in_dbg = ("move" in dbg);   swap_in_dbg = ("swap" in dbg)
   left_in_dbg = ("left" in dbg);   middle_in_dbg = ("middle" in dbg)
   right_in_dbg = ("right" in dbg)

   initialRange = range(start, len(a) if stop is None else stop)
   size         = len(initialRange) # "size" is always the length of some subarray of "a"
   stack        = TypedStack(range, maxlen=size) 
   stack.push(initialRange)
   while stack.size > 0:
      # quicksort is tail recursive: this outer loop tracks the remaining work
      currentRange = stack.pop()
      start = currentRange.start; stop = currentRange.stop; size = len(currentRange)
      if size <= max_for_insertion: # insertion sort: faster once size is around 8 or so?
         for i in range(start+1, stop):
            a_i = a[i]
            j = i - 1 # eventually j is the first element before i-th with a[i] <= a[j]
            while j>=start and cmp(a_i, a[j]) < 0: 
               a[j+1] = a[j] # shift right to make room for a_i
               j -= 1
            # j==start-1 or a[i] >= a[j]
            a[j+1] = a_i
      else:
         middle = start+ size//2
         if size<=min_for_median: partitionValue = a[middle]
         else:
            last = stop-1
            left = medianNear(start+2); middle = medianNear(middle); right = medianNear(last-2)
            # median of the medians near the start, middle, and end of the segment:
            if cmp(left,middle) < 0:
               if cmp(middle,right) < 0: partitionValue = middle
               elif cmp(left,right) < 0: partitionValue = right
               else: partitionValue = left                    
            else:
               if cmp(left,right) < 0: partitionValue = left
               elif cmp(middle,right) < 0: partitionValue = right
               else: partitionValue = middle
         firstLessOnLeft     = start       # first index that MIGHT have a value < partition
         nextLeft            = firstLessOnLeft # the next entry on the left to look at
         lastOnRight         = stop - 1    # last valid index to the right of the partition
         firstGreaterOnRight = lastOnRight # where the first > partition might be
         nextRight           = lastOnRight # the first index on the right to check
         if outer_in_dbg:
            msg = "########### start={0}, stop={1} count={2} ###########"
            print(msg.format(start, stop, stop-start))
         while True:     
            while nextLeft <= nextRight: # work in from the left
               nextLeftRelMedian = cmp(a[nextLeft], partitionValue)
               if middle_in_dbg:
                  print("left {0}: {1}>{2}?".format(nextLeft,a[nextLeft],partitionValue))
               if nextLeftRelMedian > 0: 
                  if inner_in_dbg: print("left breaking nl={0}".format(nextLeft)) 
                  break
               elif nextLeftRelMedian is 0: # push the partition value to the left end
                  temp = a[firstLessOnLeft]
                  if inner_in_dbg:
                     msg = "left: swap {0} at {1} for {2} at {3}"
                     print(msg.format(temp,firstLessOnLeft,a[nextLeft],nextLeft))
                  a[firstLessOnLeft] = a[nextLeft]
                  a[nextLeft] = temp
                  firstLessOnLeft += 1
               nextLeft += 1
            while(nextLeft <= nextRight): # work in from the right
               nextRightRelMedian = cmp(a[nextRight], partitionValue)
               if inner_in_dbg:
                  msg = "right {0}: {1}<{2}?"
                  print(msg.format(nextRight,a[nextRight],partitionValue))
               if nextRightRelMedian < 0:
                  if inner_in_dbg: print("right breaking nr={0}".format(nextRight)) 
                  break
               elif nextRightRelMedian is 0: # push the partition value to the right end
                  temp = a[firstGreaterOnRight]
                  if inner_in_dbg:
                     msg = "right: swap {0} at {1} for {2} at {3}"
                     print(msg.format(temp,firstGreaterOnRight, a[nextRight],nextRight))
                  a[firstGreaterOnRight] = a[nextRight]
                  a[nextRight] = temp
                  firstGreaterOnRight -= 1
               nextRight -= 1
            if nextLeft > nextRight:
               if middle_in_dbg: 
                  print("breaking nl={0}>nr={1}".format(nextLeft, nextRight)) 
               break
            temp = a[nextRight]
            if swap_in_dbg:
               msg = "value swap {0} at {1} for {2} at {3}"
               print(msg.format(temp,nextRight,a[nextLeft],nextLeft))
            a[nextRight] = a[nextLeft]
            a[nextLeft] = temp
            nextLeft += 1
            nextRight -= 1
            if middle_in_dbg:
               print("end while true: a="+str(a))
               msg = "{0}<{1}<{2}<{3}"
               print(msg.format(firstLessOnLeft,nextLeft,nextRight,firstGreaterOnRight))
         if outer_in_dbg:
            print("pv="+str(partitionValue)+" and a before swap="+str(a))
            print("[{0}:{1}:{2}] min({3},{4})".format(
               start, firstLessOnLeft,nextLeft,firstLessOnLeft-start,
               nextLeft-firstLessOnLeft))
            print("[{0}:{1}:{2}] min({3},{4})".format(
               nextRight, firstGreaterOnRight,lastOnRight,firstGreaterOnRight-nextRight,
               lastOnRight-firstGreaterOnRight))
         # move all the partition value entries to the middle
         valuesToMoveOnLeft = min(firstLessOnLeft-start, nextLeft-firstLessOnLeft)
         if valuesToMoveOnLeft > 0:
            firstPV = nextLeft - 1
            for i in range(0, valuesToMoveOnLeft):
               if move_in_dbg: 
                  print("{0}=s+i and {1}=fpv-i".format(start+i, firstPV-i))
               a[start+i]    = a[firstPV-i]
               a[firstPV-i] = partitionValue
         valuesToMoveOnRight = min(firstGreaterOnRight-nextRight,
                  lastOnRight-firstGreaterOnRight)
         if valuesToMoveOnRight > 0:
            firstPV = nextRight + 1
            for i in range(0, valuesToMoveOnRight):
               if move_in_dbg:
                  print("{0}=lr-i and {1}=fpv+i".format(lastOnRight-i, firstPV+i))
               a[lastOnRight-i] = a[firstPV+i]
               a[firstPV+i] = partitionValue
         leftSize  = nextLeft - firstLessOnLeft
         rightSize = firstGreaterOnRight - nextRight
         if leftSize > 1: stack.push(range(start, start+leftSize))
         if rightSize > 1: stack.push(range(stop-rightSize, stop))
   return a


Quicksort.debug = lambda commaSeparatedKeys: getDbgMgr(commaSeparatedKeys)
Quicksort.debugkeys = lambda: ["inner", "left", "middle", "move", "outer", "right", "swap"]
