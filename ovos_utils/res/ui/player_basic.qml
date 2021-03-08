/*
    * Copyright 2020 by Aditya Mehra <aix.m@outlook.com>
    *
    * Licensed under the Apache License, Version 2.0 (the "License");
    * you may not use this file except in compliance with the License.
    * You may obtain a copy of the License at
    *
    *    http://www.apache.org/licenses/LICENSE-2.0
    *
    * Unless required by applicable law or agreed to in writing, software
    * distributed under the License is distributed on an "AS IS" BASIS,
    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    * See the License for the specific language governing permissions and
    * limitations under the License.
    *
    */

import QtQuick 2.9
import QtQuick.Controls 2.3 as Controls
import QtQuick.Templates 2.12 as T
import QtQuick.Layouts 1.3
import org.kde.kirigami 2.8 as Kirigami
import QtGraphicalEffects 1.0
import Mycroft 1.0 as Mycroft

Mycroft.Delegate {
    id: root
    skillBackgroundSource: media.bg_image
    property alias thumbnail: albumimg.source
    fillWidth: true
    property int imageWidth: Kirigami.Units.gridUnit * 10
    skillBackgroundColorOverlay: Qt.rgba(0, 0, 0, 0.85)
    property bool bigMode: width > 800 && height > 600 ? 1 : 0

    // Assumption Track_Length is always in milliseconds
    // Assumption current_Position is always in milleseconds and relative to length if length = 530000, position values range from 0 to 530000

    property var media: sessionData.media
    property var compareModel
    property var playerDuration: media.length
    property real playerPosition: 0
    property var playerState: media.status
    property var nextAction: "gui.next"
    property var previousAction: "gui.previous"
    property bool countdowntimerpaused: false

    function formatedDuration(millis){
        var minutes = Math.floor(millis / 60000);
        var seconds = ((millis % 60000) / 1000).toFixed(0);
        return minutes + ":" + (seconds < 10 ? '0' : '') + seconds;
    }

    Controls.ButtonGroup {
        id: autoPlayRepeatGroup
        buttons: autoPlayRepeatGroupLayout.children
    }
    
    onPlayerStateChanged: {
        console.log(playerState)
        if(playerState === "Playing"){
            playerPosition = media.position
            countdowntimer.running = true
        } else if(playerState === "Paused") {
            playerPosition = media.position
            countdowntimer.running = false
        }
    }

    Timer {
        id: countdowntimer
        interval: 1000
        running: false
        repeat: true
        onTriggered: {
            if(media.length > playerPosition){
                if(!countdowntimerpaused){
                    playerPosition = playerPosition + 1000
                }
            }
        }
    }
    
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: bigMode ? parent.width * 0.075 : 0
        
        Rectangle {
            Layout.fillWidth: true
            Layout.minimumHeight: songtitle.contentHeight
            color: Qt.rgba(0, 0, 0, 0.8)

            Kirigami.Heading {
                id: songtitle
                text: media.title
                level: 1
                maximumLineCount: 1
                font.pixelSize: parent.width * 0.060
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                elide: Text.ElideRight
                font.capitalization: Font.Capitalize
                font.bold: true
                visible: true
                enabled: true
                width: parent.width
            }
        }
        
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "transparent"
            
            ColumnLayout {
                id: mainLayout
                anchors.fill: parent

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: "transparent"

                    Image {
                        id: albumimg
                        fillMode: Image.PreserveAspectFit
                        visible: true
                        enabled: true
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.topMargin: parent.height * 0.05
                        anchors.bottomMargin: parent.height * 0.05
                        source: media.image
                        layer.enabled: true
                        layer.effect: DropShadow {
                            horizontalOffset: 1
                            verticalOffset: 2
                            spread: 0.2
                        }
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true


                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 150
                        Layout.preferredWidth:parent.width
                        color: "transparent"

                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: Kirigami.Units.largeSpacing
                            spacing: Kirigami.Units.largeSpacing * 2

                            Controls.Button {
                                id: previousButton
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                Layout.alignment: Qt.AlignVCenter
                                focus: false
                                KeyNavigation.right: playButton
                                KeyNavigation.down: seekableslider
                                onClicked: {
                                    triggerGuiEvent(previousAction, {})
                                }

                                contentItem: Kirigami.Icon {
                                    source: Qt.resolvedUrl("images/media-seek-backward.svg")
                                }

                                background: Rectangle {
                                    color: "transparent"
                                }

                                Keys.onReturnPressed: {
                                    clicked()
                                }
                            }

                            Controls.Button {
                                id: playButton
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                Layout.alignment: Qt.AlignVCenter
                                onClicked: {
                                    if (playerState != "Playing"){
                                        console.log("in resume action")
                                        triggerGuiEvent("gui.play", {"media": {
                                                                "image": media.image,
                                                                "track": media.track,
                                                                "album": media.album,
                                                                "skill": media.skill,
                                                                "length": media.length,
                                                                "position": playerPosition,
                                                                "status": "Playing"}})
                                    } else {
                                        triggerGuiEvent("gui.pause", {"media": {
                                                                "image": media.image,
                                                                "title": media.title,
                                                                "album": media.album,
                                                                "skill_id":media.skill,
                                                                "length": media.length,
                                                                "position": playerPosition,
                                                                "status": "Paused"}})
                                    }
                                }

                                background: Rectangle {
                                    color: "transparent"
                                }

                                contentItem: Kirigami.Icon {
                                    source: playerState === "Playing" ? Qt.resolvedUrl("images/media-playback-pause.svg") : Qt.resolvedUrl("images/media-playback-start.svg")
                                }
                            }

                            Controls.Button {
                                id: nextButton
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                Layout.alignment: Qt.AlignVCenter
                                onClicked: {
                                    triggerGuiEvent(nextAction, {})
                                }

                                background: Rectangle {
                                    color: "transparent"
                                }

                                contentItem: Kirigami.Icon {
                                    source: Qt.resolvedUrl("images/media-seek-forward.svg")
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
