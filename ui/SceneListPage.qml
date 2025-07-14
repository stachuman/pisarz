import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Page {
    id: sceneListPage
    title: qsTr("Scenes")

    property string projectPath: ""
    property string projectName: ""

    header: Rectangle {
        height: 60
        color: "#2c3e50"
        
        RowLayout {
            anchors.fill: parent
            anchors.margins: 10
            
            Button {
                text: qsTr("← Projects")
                onClicked: stackView.pop()
            }
            
            Text {
                text: qsTr("Scenes - %1").arg(projectName)
                color: "white"
                font.pixelSize: 18
                font.bold: true
                Layout.fillWidth: true
            }
            
            Button {
                text: qsTr("New Scene")
                onClicked: newSceneDialog.open()
            }
        }
    }

    GridView {
        id: scenesGrid
        anchors.fill: parent
        anchors.margins: 20
        cellWidth: 250
        cellHeight: 150
        model: scenesModel

        delegate: Rectangle {
            width: scenesGrid.cellWidth - 10
            height: scenesGrid.cellHeight - 10
            color: "#ecf0f1"
            border.color: "#bdc3c7"
            border.width: 1
            radius: 5

            MouseArea {
                anchors.fill: parent
                onClicked: {
                    stackView.push("SceneEditorPage.qml", {
                        "sceneId": model.id,
                        "sceneBridge": sceneBridge
                    })
                }
            }

            Column {
                anchors.fill: parent
                anchors.margins: 15
                spacing: 10

                Text {
                    text: model.title || qsTr("Untitled Scene")
                    font.pixelSize: 14
                    font.bold: true
                    color: "#2c3e50"
                    width: parent.width
                    wrapMode: Text.WordWrap
                    maximumLineCount: 2
                    elide: Text.ElideRight
                }

                Rectangle {
                    width: parent.width
                    height: 1
                    color: "#bdc3c7"
                }

                Text {
                    text: {
                        if (model.content_rtf && model.content_rtf.length > 0) {
                            var preview = model.content_rtf.substring(0, 100)
                            if (model.content_rtf.length > 100) preview += "..."
                            return preview
                        }
                        return qsTr("Empty scene")
                    }
                    font.pixelSize: 11
                    color: "#7f8c8d"
                    width: parent.width
                    height: parent.height - 40
                    wrapMode: Text.WordWrap
                    elide: Text.ElideRight
                }

                Text {
                    text: qsTr("Scene %1").arg(model.ord || 0)
                    font.pixelSize: 10
                    color: "#95a5a6"
                    anchors.right: parent.right
                }
            }
        }
    }

    Text {
        anchors.centerIn: parent
        text: qsTr("No scenes yet. Click 'New Scene' to create your first scene.")
        color: "#7f8c8d"
        font.pixelSize: 14
        visible: scenesGrid.count === 0
    }

    Dialog {
        id: newSceneDialog
        title: qsTr("Create New Scene")
        width: 400
        height: 200
        anchors.centerIn: parent
        modal: true

        Column {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 20

            Text {
                text: qsTr("Scene Title:")
                font.pixelSize: 14
            }

            TextField {
                id: sceneNameField
                width: parent.width
                placeholderText: qsTr("Enter scene title...")
            }

            Row {
                anchors.right: parent.right
                spacing: 10

                Button {
                    text: qsTr("Cancel")
                    onClicked: {
                        sceneNameField.text = ""
                        newSceneDialog.close()
                    }
                }

                Button {
                    text: qsTr("Create")
                    enabled: sceneNameField.text.trim().length > 0
                    onClicked: {
                        if (sceneNameField.text.trim().length > 0) {
                            sceneBridge.createScene(sceneNameField.text.trim())
                            sceneNameField.text = ""
                            newSceneDialog.close()
                        }
                    }
                }
            }
        }
    }

    Component.onCompleted: {
        if (sceneBridge && projectPath) {
            sceneBridge.setProjectPath(projectPath)
            sceneBridge.refreshScenes()
        }
    }
}
