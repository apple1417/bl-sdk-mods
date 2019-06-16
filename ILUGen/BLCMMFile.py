class _ChildArray:
    def __init__(self):
        self._children = []
    
    def addChild(self, child):
        self._children.append(child)
    
    def removeChild(self, child):
        self._children.remove(child)
    
    def getChild(self, index):
        return self._children[index]

class ModFile(_ChildArray):
    def __init__(self, name, isBL2):
        _ChildArray.__init__(self)
        self.name = name
        self.isBL2 = isBL2
    
    def toFile(self, filePath):
        if not filePath.endswith(".blcm"):
            filePath += ".blcm"
        with open(filePath, "w") as file:
            file.write("<BLCMM v=\"1\">\n")
            file.write("#<!!!You opened a file saved with BLCMM in FilterTool. Please update to BLCMM to properly open this file!!!>\n")
            file.write("\t<head>\n")
            if self.isBL2:
                file.write("\t\t<type name=\"BL2\" offline=\"false\"/>\n")
            else:
                file.write("\t\t<type name=\"TPS\" offline=\"false\"/>\n")
            file.write("\t\t<profiles>\n")
            file.write("\t\t\t<profile name=\"default\" current=\"true\"/>\n")
            file.write("\t\t</profiles>\n")
            file.write("\t</head>\n")
            file.write("\t<body>\n")
            file.write(f"\t\t<category name=\"{self.name}\">\n")
            for child in self._children:
                file.write("\t\t\t" + child.toString().replace("\n", "\n\t\t\t") + "\n")
            file.write(f"\t\t</category>\n")
            file.write(f"\t</body>\n")
            file.write(f"</BLCMM>\n")

class Category(_ChildArray):
    def __init__(self, name):
        _ChildArray.__init__(self)
        self.name = name

    def toString(self):
        output = f"<category name=\"{self.name}\">\n"
        for child in self._children:
            output += "\t" + child.toString().replace("\n", "\n\t") + "\n"
        output += "</category>"
        return output

class Hotfix(_ChildArray):
    def __init__(self, name, level=None, package=None):
        _ChildArray.__init__(self)
        self.name = name
        self.level = level
        self.package = package if level == None else None
        
    def toString(self):
        hotfixType = ""
        if self.level != None:
            hotfixType = f" level=\"{self.level}\""
        elif self.package != None:
            hotfixType = f" package=\"{self.package}\""
        
        output = f"<hotfix name=\"{self.name}\"{hotfixType}>\n"
        for child in self._children:
            output += "\t" + child.toString().replace("\n", "\n\t") + "\n"
        output += "</hotfix>"
        return output

class Comment:
    def __init__(self, comment):
        self.comment = comment
    
    def toString(self):
        return f"<comment>{self.comment}</comment>"

class Command:
    def __init__(self, object, field, value):
        self.object = object
        self.field = field
        self.value = value
    
    def toString(self):
        return f"<code profiles=\"default\">set {self.object} {self.field} {self.value}</code>"