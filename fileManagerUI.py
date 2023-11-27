import os.path
from datetime import datetime
import maya.cmds as cmds

class FileInfo:
    def __init__(self, file_path):
        self.path = file_path
        file_name = os.path.basename(file_path)
        info = file_name.split("_")
        print(info)

        #check if file is published, in that case the naming structure would be different
        published=False
        if info[-1]=='publish.ma':
            published = True

        self.projectTag = info[0]
        self.fileType = info[1]
        self.name = info[2]
        if not published:
            print("AAAA")
            self.task = info[3]
            self.version = info[4]
            self.initials = info[5].split(".")[0]
        else:
            self.task = info[3]

def reloadSceneReferences(*args):
    name = cmds.file(save=True, force=True)
    cmds.file(name, open=True)

def listPublishedItems():
    project_path = cmds.workspace(rootDirectory=True,q=True, dir=True)+"assets/prp/"
    #print(project_path)
    result = []
    for root,dirs,files in os.walk(project_path):
        #if os.path.basename(dirs = "published")
        #print(root)
        for name in files:
            if name.endswith("_publish.ma") and os.path.getsize(os.path.join(root,name))>0:
                result.append(FileInfo(os.path.join(root, name)))

    print (result[0].task)
    last_modified = os.path.getmtime(result[0].path)
    last_modified_date = datetime.fromtimestamp(last_modified).strftime("%H:%M:%S\n%d/%m/%Y")
    print (last_modified_date)
    return result


def publish(file):
    source_file = cmds.file(query=True, sn=True)
    file = FileInfo(source_file)
    publish_template = "{projectTag}_{fileType}_{name}_{task}_publish"
    publish_file = publish_template.format(projectTag=file.projectTag, fileType=file.fileType, name=file.name,
                                           task=file.task)

    publish_path = os.path.dirname(os.path.dirname(file.path))+"/publish/"+publish_file
    print(publish_path)

    #confirmation window
    confirmation = cmds.confirmDialog(title='Confirm', message='Going to publish in '+publish_path+" are you sure you want to continue?",
                       button=['Yes', 'No'], defaultButton='Yes',cancelButton='No', dismissString='No')
    if confirmation == 'Yes':
        cmds.file(publish_path, es=True, force=True, ch=False, typ="mayaAscii")


def createReference(table,assets):
    selection = cmds.scriptTable(table, q=True, selectedRow=True)
    cmds.file(assets[selection-1].path,reference=True, ignoreVersion=True, namespace=assets[selection-1].fileType+"_"+assets[selection-1].name)
    print(selection)


def cellChangedCB(pRow, pClm, pValue):
   return 1


def createWin():
    win = "scriptWin"
    name = "Exporter"

    if cmds.window(win, exists=True):
        cmds.deleteUI(win, window=True)
    # create window
    win = cmds.window(win, title=name)

    cmds.columnLayout(adjustableColumn=True)
    cmds.text(name, al='left')
    cmds.separator(height=20)

    # create assets table
    assets = listPublishedItems()

    table = cmds.scriptTable(rows=len(assets), columns=2, editable=False, label=[(1, "File"), (2, "Date Modified")], ccc=cellChangedCB)
    for i in range(len(assets)):
        cmds.scriptTable(table, e=True,ci=[1+i,1],cv = assets[i].name)
        last_modified = os.path.getmtime(assets[i].path)
        last_modified_date = datetime.fromtimestamp(last_modified).strftime("%H:%M:%S\n%d/%m/%Y")
        cmds.scriptTable(table, e=True, ci=[1+i,2], cv=last_modified_date)

    #cmds.columnLayout(columnAttach=('both', 5), rowSpacing=10)
    form = cmds.formLayout(numberOfDivisions=100)
    b1 = cmds.button(label="Reference Asset", command=lambda *args: createReference(table,assets))
    b2 = cmds.button(label="Reload References", command=reloadSceneReferences)
    b3 = cmds.button(label="Publish Asset", command=publish)
    cmds.formLayout(form, edit=True, attachForm=[(b1,'top',5),(b1, 'left', 5), (b2,'top',5),(b2, 'right', 5), (b3,'left',5), (b3,'bottom',5), (b3,'right',5)],
                    attachControl=[(b1, 'bottom', 5, b3),(b2, 'bottom', 5, b3)],
                    attachPosition=[(b1, 'right', 0, 49), (b2, 'left', 0, 51)],
                    attachNone=(b3, 'top'))


    # show window
    cmds.showWindow(win)