/* === This file is part of EasyArch - <https://gitlab.com/easyarch-iso> ===
 *
 *   Copyright 2020, Asif Mahmud Shimon <ams.eee09@gmail.com>
 *
 *   EasyArch is free software: you can redistribute it and/or modify
 *   it under the terms of the GNU General Public License as published by
 *   the Free Software Foundation, either version 3 of the License, or
 *   (at your option) any later version.
 *
 *   EasyArch is distributed in the hope that it will be useful,
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 *   GNU General Public License for more details.
 *
 *   You should have received a copy of the GNU General Public License
 *   along with EasyArch. If not, see <http://www.gnu.org/licenses/>.
 */
import QtQuick 2.0
import calamares.slideshow 1.0
import QtQuick.Layouts 1.11

Presentation {
    id: presentation

    function nextSlide() {
        console.log("QML Component (default slideshow) Next slide")
        presentation.goToNextSlide()
    }

    Timer {
        id: advanceTimer
        interval: 10 * 1000
        running: presentation.activatedInCalamares
        repeat: true
        onTriggered: nextSlide()
    }

    Slide {
        anchors.rightMargin: 0
        anchors.bottomMargin: 0
        anchors.leftMargin: 0
        anchors.topMargin: 0
        anchors.fill: parent

        RowLayout {
            id: rowLayout1
            anchors.fill: parent
            spacing: 0
            Rectangle {
                id: blueRect1
                color: "#4A65BD"
                Layout.fillHeight: true
                Layout.fillWidth: true
                border.width: 0

                Text {
                    id: slide1Text1
                    color: "#161720"
                    text: qsTr("virOS")
                    font.pointSize: 64
                    styleColor: "#161720"
                    horizontalAlignment: Text.AlignRight
                    verticalAlignment: Text.AlignVCenter
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.right: parent.right
                    anchors.rightMargin: 0
                }
            }

            Rectangle {
                id: darkRect1
                color: "#161720"
                Layout.fillHeight: true
                Layout.fillWidth: true
                border.width: 0

                Text {
                    id: slide1Text2
                    color: "#4A65BD"
                    text: qsTr("Linux")
                    font.pointSize: 64
                    styleColor: "#4A65BD"
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.left: parent.left
                    anchors.leftMargin: 0
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignLeft
                }
            }
        }
    }
    Slide {
        anchors.rightMargin: 0
        anchors.fill: parent
        anchors.bottomMargin: 0
        anchors.topMargin: 0
        anchors.leftMargin: 0
        RowLayout {
            id: rowLayout2
            anchors.fill: parent
            spacing: 0
            Rectangle {
                id: blueRect2
                color: "#4A65BD"
                Layout.fillHeight: true
                Layout.fillWidth: true
                border.width: 0

                Text {
                    id: slide2Text1
                    width: parent.width / 2
                    color: "#161720"
                    text: qsTr("virOS Linux Home")
                    anchors.horizontalCenter: parent.horizontalCenter
                    font.pointSize: 20
                    wrapMode: Text.WordWrap
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                    anchors.verticalCenter: parent.verticalCenter
                }
            }

            Rectangle {
                id: darkRect2
                color: "#161720"
                Layout.fillHeight: true
                Layout.fillWidth: true
                border.width: 0

                Text {
                    id: slide2Text2
                    color: "#4A65BD"
                    text: "https://git.io/virOS"
                    style: Text.Raised
                    font.underline: true
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.verticalCenter: parent.verticalCenter
                    font.pointSize: 20
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WrapAnywhere

                    MouseArea {
                        id: slide2Text2MouseArea
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor

                        onClicked: {
                            Qt.openUrlExternally("https://virOS.github.io")
                        }
                    }
                }
            }
        }
    }
    Slide {
        anchors.rightMargin: 0
        anchors.fill: parent
        anchors.bottomMargin: 0
        anchors.topMargin: 0
        anchors.leftMargin: 0
        RowLayout {
            id: rowLayout3
            anchors.fill: parent
            spacing: 0
            Rectangle {
                id: darkRect3
                color: "#161720"
                Layout.fillHeight: true
                Layout.fillWidth: true
                border.width: 0

                Text {
                    id: slide3Text1
                    width: parent.width / 2
                    color: "#4A65BD"
                    text: qsTr("Forum virOS")
                    anchors.horizontalCenter: parent.horizontalCenter
                    font.pointSize: 20
                    wrapMode: Text.WordWrap
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                    anchors.verticalCenter: parent.verticalCenter
                }
            }

            Rectangle {
                id: blueRect3
                color: "#4A65BD"
                Layout.fillHeight: true
                Layout.fillWidth: true
                border.width: 0

                Text {
                    id: slide3Text2
                    color: "#161720"
                    text: "forum.virOS.ru"
                    style: Text.Raised
                    font.underline: true
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.verticalCenter: parent.verticalCenter
                    font.pointSize: 20
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WrapAnywhere

                    MouseArea {
                        id: slide3Text2MouseArea
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor

                        onClicked: {
                            Qt.openUrlExternally("https://forum.virOS.ru")
                        }
                    }
                }
            }
        }
    }
    Slide {
        anchors.rightMargin: 0
        anchors.fill: parent
        anchors.bottomMargin: 0
        anchors.topMargin: 0
        anchors.leftMargin: 0
        RowLayout {
            id: rowLayout4
            anchors.fill: parent
            spacing: 0
            Rectangle {
                id: blueRect4
                color: "#4A65BD"
                Layout.fillHeight: true
                Layout.fillWidth: true
                border.width: 0

                Text {
                    id: slide4Text1
                    width: parent.width / 2
                    color: "#161720"
                    text: qsTr("Telegram Chat")
                    anchors.horizontalCenter: parent.horizontalCenter
                    font.pointSize: 20
                    wrapMode: Text.WordWrap
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                    anchors.verticalCenter: parent.verticalCenter
                }
            }

            Rectangle {
                id: darkRect4
                color: "#161720"
                Layout.fillHeight: true
                Layout.fillWidth: true
                border.width: 0

                Text {
                    id: slide4Text2
                    color: "#4A65BD"
                    text: "telegram.me/virOS"
                    style: Text.Raised
                    font.underline: true
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.verticalCenter: parent.verticalCenter
                    font.pointSize: 20
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WrapAnywhere

                    MouseArea {
                        id: slide4Text2MouseArea
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor

                        onClicked: {
                            Qt.openUrlExternally("https://telegram.me/virOS")
                        }
                    }
                }
            }
        }
    }
    Slide {
        anchors.rightMargin: 0
        anchors.fill: parent
        anchors.bottomMargin: 0
        anchors.topMargin: 0
        anchors.leftMargin: 0
        RowLayout {
            id: rowLayout5
            anchors.fill: parent
            spacing: 0
            Rectangle {
                id: darkRect5
                color: "#161720"
                Layout.fillHeight: true
                Layout.fillWidth: true
                border.width: 0

                Text {
                    id: slide5Text1
                    width: parent.width / 2
                    color: "#4A65BD"
                    text: qsTr("Vk virOS")
                    anchors.horizontalCenter: parent.horizontalCenter
                    font.pointSize: 20
                    wrapMode: Text.WordWrap
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                    anchors.verticalCenter: parent.verticalCenter
                }
            }

            Rectangle {
                id: blueRect5
                color: "#4A65BD"
                Layout.fillHeight: true
                Layout.fillWidth: true
                border.width: 0

                Text {
                    id: slide5Text2
                    color: "#161720"
                    text: "vk.com/virOS"
                    style: Text.Raised
                    font.underline: true
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.verticalCenter: parent.verticalCenter
                    font.pointSize: 20
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WrapAnywhere

                    MouseArea {
                        id: slide5Text2MouseArea
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor

                        onClicked: {
                            Qt.openUrlExternally("https://vk.com/virOS")
                        }
                    }
                }
            }
        }
    }
    Slide {
        anchors.rightMargin: 0
        anchors.fill: parent
        anchors.bottomMargin: 0
        anchors.topMargin: 0
        anchors.leftMargin: 0
        RowLayout {
            id: rowLayout6
            anchors.fill: parent
            spacing: 0
            Rectangle {
                id: blueRect6
                color: "#4A65BD"
                Layout.fillHeight: true
                Layout.fillWidth: true
                border.width: 0

                Text {
                    id: slide6Text1
                    width: parent.width / 2
                    color: "#161720"
                    text: qsTr("Github virOS")
                    anchors.horizontalCenter: parent.horizontalCenter
                    font.pointSize: 20
                    wrapMode: Text.WordWrap
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                    anchors.verticalCenter: parent.verticalCenter
                }
            }

            Rectangle {
                id: darkRect6
                color: "#161720"
                Layout.fillHeight: true
                Layout.fillWidth: true
                border.width: 0

                Text {
                    id: slide6Text2
                    color: "#4A65BD"
                    text: "github.com/virOS"
                    style: Text.Raised
                    font.underline: true
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.verticalCenter: parent.verticalCenter
                    font.pointSize: 20
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WrapAnywhere

                    MouseArea {
                        id: slide6Text2MouseArea
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor

                        onClicked: {
                            Qt.openUrlExternally("https://github.com/virOS")
                        }
                    }
                }
            }
        }
    }
    Slide {
        anchors.rightMargin: 0
        anchors.bottomMargin: 0
        anchors.leftMargin: 0
        anchors.topMargin: 0
        anchors.fill: parent

        RowLayout {
            id: rowLayout7
            anchors.fill: parent
            spacing: 0
            Rectangle {
                id: darkRect7
                color: "#161720"
                Layout.fillHeight: true
                Layout.fillWidth: true
                border.width: 0

                Text {
                    id: slide7Text1
                    color: "#4A65BD"
                    text: qsTr("© 2017 ")
                    font.pointSize: 32
                    styleColor: "#4A65BD"
                    horizontalAlignment: Text.AlignRight
                    verticalAlignment: Text.AlignVCenter
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.right: parent.right
                    anchors.rightMargin: 0
                }
            }

            Rectangle {
                id: blueRect7
                color: "#4A65BD"
                Layout.fillHeight: true
                Layout.fillWidth: true
                border.width: 0

                Text {
                    id: slide7Text2
                    color: "#161720"
                    text: qsTr(" Alex Creio")
                    font.pointSize: 32
                    styleColor: "#161720"
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.left: parent.left
                    anchors.leftMargin: 0
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignLeft
                }
            }
        }
    }
    function onActivate() {
        console.log("QML Component (default slideshow) activated")
        presentation.currentSlide = 0
    }

    function onLeave() {
        console.log("QML Component (default slideshow) deactivated")
    }
}
