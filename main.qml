import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.12

ApplicationWindow {
    visible: true
    width: 600*2
    height: 400*2
    title: "LyriX"
    id: main

    property QtObject backend

    Image {
        id: imgCover
        height: 380
        width: 380

        source: "./background.png"
        smooth: true
        mipmap: true
    }

    Rectangle {
        id: backgroundRectangle
        anchors.fill: parent
        color: "#fff"

        Rectangle {
            color: "transparent"
            height: 450
            width: 450
            anchors.centerIn: parent
            opacity: 0.5

            GaussianBlur {
                anchors.centerIn: parent
                height: imgCover.height
                width: imgCover.width
                source: imgCover
                radius: 8
                samples: 16
                deviation: 4
                transparentBorder: true
            }
        }

        Rectangle {
            anchors.fill: parent
            color: "#34000000"
            
            ListView {
                anchors.fill:parent

                model: lyrics
                id:listview

                delegate: Text {
                    text: textLyric
                    font.pixelSize: selected ? 60 : 40
                    font.family: spotifyFont.name
                    font.letterSpacing: -1.5
                    color: selected ? "#ddffffff" : "#dd000000"
                    width: listview.width
                    padding: 13
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                    visible: !hidden
                }
            }
        }
    }

    Connections {
        target: backend
        
        function onClearLyrics() {
            lyrics.clear();
            for (let i = 0; i < 50 ; i++) 
                lyrics.set(i, {"textLyric": "", "selected": false, "hidden": true});
        }

        function onAddLyric(index, text){
            index = index + 50;
            lyrics.set(index, {"textLyric": text, "selected": false, "hidden": true});
        }

        function onSelectLine(index){
            index = index + 50;
            for (let i = 0; i < lyrics.count ; i++) {
                lyrics.setProperty(i, "selected", false)
                if(i == index-1 || i == index+1)
                    lyrics.setProperty(i, "hidden", false)
                else
                    lyrics.setProperty(i, "hidden", true)
            }
            lyrics.setProperty(index, "hidden", false)
            lyrics.setProperty(index, "selected", true)
            listview.positionViewAtIndex(index, ListView.Center)
        }
        
        function onUpdateColor(background, text){
            backgroundRectangle.color = background;
        }

        function onUpdateCover(imgUrl){
            imgCover.source = imgUrl;
        }
    }

    ListModel {
        id: lyrics
    }

    FontLoader { id: spotifyFont; source: "CircularStd-Black.otf" }
}