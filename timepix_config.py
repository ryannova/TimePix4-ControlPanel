import os

class tp4_config:
    _comment_tag = "*"
    _separator_tag = ":"
    def __init__(self, filename) -> None:
        self.filename = filename

    def make(self, data_dict, preface="") -> bool:
        file = open(self.filename, "w")
        for k in data_dict:
            file.write("{}: {}\n".format(k, data_dict[k]))
        file.close()


    def parse(self) -> dict:
        file = open(self.filename, "r")
        line = file.readline()
        self.data_dict = {}
        data_stack = [self.data_dict]
        while line:
            if line[0] == self._comment_tag:
                line = file.readline()
                continue
            preface_index = 0

            key = line[0:line.find(":")].replace("\n", "")
            value = line[line.find(":")+1:].replace("\n", "") 
            
            data_stack[preface_index][key] = value
            line = file.readline()
        file.close()

if __name__ == "__main__":
    config = tp4_config("test.config")
    config.make({"key": "value", "key2": "value"})
    config.parse()
    os.remove("test.config")
    print(config.data_dict)