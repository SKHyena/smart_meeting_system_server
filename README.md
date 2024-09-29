# Smart Meeting System server

Api server setup & execution guide for smart meeting system

## 요구사항 (Prerequisites)

이 프로젝트를 실행하려면 아래의 소프트웨어가 필요합니다:

- [Docker](https://www.docker.com/get-started) 
- [Docker Compose](https://docs.docker.com/compose/install/)

## 클론 및 설정

### 1. 저장소 클론
먼저 이 저장소를 로컬에 클론하세요.

```bash
git clone https://github.com/SKHyena/smart_meeting_system_server.git
cd smart_meeting_system_server
```

### 2. Docker 이미지 빌드
Dockerfile을 기반으로 Docker 이미지를 빌드합니다.

```bash
docker build -t smart_meeting_system_server .
```

### 3. Docker Compose 실행
docker-compose.yml을 기반으로 api server를 실행시키기 위해 Docker Compose를 실행합니다.

```bash
docker-compose up
```

Background 실행을 위해서는 -d 옵션을 사용하세요.
```bash
docker-compose up -d
```

실행 중지
```bash
docker-compose down
```
