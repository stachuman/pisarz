import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Page {
    id: projectListPage
    title: qsTr("Projects")

    header: Rectangle {
        height: 60
        color: "#2c3e50"
        
        RowLayout {
            anchors.fill: parent
            anchors.margins: 10
            
            Text {
                text: qsTr("Pisarz - Projects")
                color: "white"
                font.pixelSize: 18
                font.bold: true
                Layout.fillWidth: true
            }
            
            Button {
                text: qsTr("New Project")
                onClicked: newProjectDialog.open()
            }
        }
    }

    ListView {
        id: projectsList
        anchors.fill: parent
        anchors.margins: 20
        spacing: 10
        model: projectsModel

        delegate: Rectangle {
            width: projectsList.width
            height: 80
            color: "#ecf0f1"
            border.color: "#bdc3c7"
            border.width: 1
            radius: 5

            MouseArea {
                anchors.fill: parent
                onClicked: {
                    stackView.push("SceneListPage.qml", {
                        "projectPath": model.path,
                        "projectName": model.name
                    })
                }
            }

            Column {
                anchors.left: parent.left
                anchors.leftMargin: 15
                anchors.verticalCenter: parent.verticalCenter
                spacing: 5

                Text {
                    text: model.name || ""
                    font.pixelSize: 16
                    font.bold: true
                    color: "#2c3e50"
                }

                Text {
                    text: qsTr("Created: %1").arg(model.created_at || "")
                    font.pixelSize: 12
                    color: "#7f8c8d"
                }
            }
        }
    }

    Text {
        anchors.centerIn: parent
        text: qsTr("No projects yet. Click 'New Project' to create your first project.")
        color: "#7f8c8d"
        font.pixelSize: 14
        visible: projectsList.count === 0
    }

    Dialog {
        id: newProjectDialog
        title: qsTr("Create New Project")
        width: 400
        height: 200
        anchors.centerIn: parent
        modal: true

        Column {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 20

            Text {
                text: qsTr("Project Name:")
                font.pixelSize: 14
            }

            TextField {
                id: projectNameField
                width: parent.width
                placeholderText: qsTr("Enter project name...")
            }

            Row {
                anchors.right: parent.right
                spacing: 10

                Button {
                    text: qsTr("Cancel")
                    onClicked: {
                        projectNameField.text = ""
                        newProjectDialog.close()
                    }
                }

                Button {
                    text: qsTr("Create")
                    enabled: projectNameField.text.trim().length > 0
                    onClicked: {
                        if (projectNameField.text.trim().length > 0) {
                            projectManager.createProject(projectNameField.text.trim())
                            projectNameField.text = ""
                            newProjectDialog.close()
                        }
                    }
                }
            }
        }
    }


    Component.onCompleted: {
        if (projectManager) {
            projectManager.refreshProjects()
        }
    }
}