datafiles = ["pyqtgraph", "pyqtgraph_100points", "matplot", "matplot_100points"]
for program_type in datafiles:
    with open("/home/r/TIMEPIX/data_%s.txt" % (program_type), "r") as f:
        line = f.readline().strip("\n")
        total = float(line)
        counter = 1.0
        while line:
            total += float(line)
            counter += 1.0
            line = f.readline().strip("\n")
        print("Average time required to run %s %f" % (program_type, total/counter))