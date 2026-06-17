"""노트북 기능 조립 계층.

FastAPI dependency, domain service, infrastructure adapter 사이의 구현체 선택을
한곳에 모은다. 서비스 파일은 비즈니스 흐름에, infrastructure 파일은 실제 I/O 구현에
집중하고, 이 패키지는 어떤 구현을 쓸지 결정한다.
"""
