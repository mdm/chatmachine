part1 = open('Bronze.trail.txt').readlines()
part2 = open('trail2.txt').readlines()

smax = 0
start1 = 0
for line1 in part1:
    if line1 == part2[0]:
        start2 = 0
        for line2 in part1[start1:]:
            if not line2 == part2[start2]:
                break
            start2 += 1
        if start2 > smax:
            print start1, start2, start1 + start2
            smax = start2
    start1 += 1
   
