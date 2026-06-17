from typing import TypeVar

from fastapi.params import Depends as DependsClass

T = TypeVar("T")


def autowired[T](cls: type[T]) -> type[T]:
    """dataclass 서비스의 Depends 필드를 자동으로 언래핑 및 해석해주는 데코레이터.
    
    인스턴스 생성 시 필드 기본값에 Depends가 지정되어 있을 때,
    그 값이 DependsClass 인스턴스인 경우 실제 의존성 팩토리 함수를 호출하여 주입해 줍니다.
    """
    original_post_init = getattr(cls, "__post_init__", None)

    def new_post_init(self, *args, **kwargs):
        # __dataclass_fields__ 가 존재하면 해당 필드들을 순회하며 DependsClass인 경우 언래핑
        for field_name in getattr(self, "__dataclass_fields__", {}):
            val = getattr(self, field_name)
            if isinstance(val, DependsClass):
                dep_func = val.dependency
                if dep_func is not None:
                    # 의존성 팩토리 함수를 호출하여 결과 주입
                    setattr(self, field_name, dep_func())
        
        if original_post_init is not None:
            original_post_init(self, *args, **kwargs)

    cls.__post_init__ = new_post_init
    return cls
