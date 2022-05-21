properties([
   buildDiscarder(logRotator(numToKeepStr: '20')),
   disableConcurrentBuilds()
])

node('SD-RM') {
    init()
    test()
}

def init() {
    // git should use the Windows Store (certificates), but this fails sometimes
    bat 'git config --global http.sslVerify false'
    checkout scm
}

def test() {
    stage('test') {
        bat 'build.bat'
        junit allowEmptyResults: false, keepLongStdio: false, testResults: 'output/test-report.xml'
    }
}
