from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q


from django.utils.decorators import method_decorator
from django.views import View

from .models import Post, UserProfile, UserProfile, ChatRoom, Message

from .forms import CustomLoginForm, CustomRegistrationForm, PostForm, UserProfileForm


# 채팅테스트
# chat/views.py
from django.shortcuts import render


def index(request):
    return render(request, "chat/index.html")
# 채팅방 열기
def chat_room(request, pk):
    user = request.user
    chat_room = get_object_or_404(ChatRoom, pk=pk)

    # 내 ID가 포함된 방만 가져오기
    chat_rooms = ChatRoom.objects.filter(
            Q(receiver_id=user) | Q(starter_id=user)
        ).order_by('-latest_message_time')  # 최신 메시지 시간을 기준으로 내림차순 정렬
    
    # 각 채팅방의 최신 메시지를 가져오기
    chat_room_data = []
    for room in chat_rooms:
        latest_message = Message.objects.filter(chatroom=room).order_by('-timestamp').first()
        if latest_message:
            chat_room_data.append({
                'chat_room': room,
                'latest_message': latest_message.content,
                'timestamp': latest_message.timestamp,
            })

    # 상대방 정보 가져오기
    if chat_room.receiver == user:
        opponent = chat_room.starter
    else:
        opponent = chat_room.receiver

    opponent_user = User.objects.get(pk=opponent.pk)


    # post의 상태 확인 및 처리
    if chat_room.post is None:
        seller = None
        post = None
    else:
        seller = chat_room.post.user
        post = chat_room.post

    return render(request, 'dangun_app/chat_room.html', {
        'chat_room': chat_room,
        'chat_room_data': chat_room_data,
        'room_name': chat_room.pk,
        'seller': seller,
        'post': post,
        'opponent': opponent_user,
    })


# 채팅방 생성 또는 참여
def create_or_join_chat(request, pk):
    post = get_object_or_404(Post, pk=pk)
    user = request.user
    chat_room = None
    created = False

    # 채팅방이 이미 존재하는지 확인
    chat_rooms = ChatRoom.objects.filter(
        Q(starter=user, receiver=post.user, post=post) |
        Q(starter=post.user, receiver=user, post=post)
    )
    if chat_rooms.exists():
        chat_room = chat_rooms.first()
    else:
        # 채팅방이 존재하지 않는 경우, 새로운 채팅방 생성
        chat_room = ChatRoom(starter=user, receiver=post.user, post=post)
        chat_room.save()
        created = True

    return JsonResponse({'success': True, 'chat_room_id': chat_room.pk, 'created': created})


# 가장 최근 채팅방 가져오기
@login_required
def get_latest_chat(request, pk):
    user = request.user
    # 1) 해당 pk인 채팅방 중 가장 최신 채팅방으로 리디렉션
    try:
        latest_chat_with_pk = ChatRoom.objects.filter(
            Q(post_id=pk) &
            (Q(receiver=user) | Q(starter=user))
        ).latest('latest_message_time')
        return JsonResponse({'success': True, 'chat_room_id': latest_chat_with_pk.room_number})
    except ChatRoom.DoesNotExist:
        pass

    # 2) 위 경우가 없다면 내가 소속된 채팅방 전체 중 가장 최신 채팅방으로 리디렉션
    try:
        latest_chat = ChatRoom.objects.filter(
            Q(receiver=user) | Q(starter=user)
        ).latest('latest_message_time')
        return JsonResponse({'success': True, 'chat_room_id': latest_chat.room_number})

    # 3) 모두 없다면 현재 페이지로 리디렉션
    except ChatRoom.DoesNotExist:
        return redirect('dangun_app:alert', alert_message='진행중인 채팅이 없습니다.')
        
# nav/footer에서 채팅하기 눌렀을 때
@login_required
def get_latest_chat_no_pk(request):
    user = request.user
    try:
        latest_chat = ChatRoom.objects.filter(
            Q(receiver=user) | Q(starter=user),
            latest_message_time__isnull=False
        ).latest('latest_message_time')
        return redirect('dangun_app:chat_room', pk=latest_chat.room_number)

    except ChatRoom.DoesNotExist:
        return redirect('dangun_app:alert', alert_message='진행중인 채팅이 없습니다.')
    
@method_decorator(login_required, name='dispatch')
class ConfirmDealView(View):
    def post(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id)
        user = request.user

        previous_url = request.META.get('HTTP_REFERER')
        url_parts = previous_url.split('/')
        original_post_id = url_parts[-2] if url_parts[-1] == '' else url_parts[-1]

        chat_room = get_object_or_404(ChatRoom, room_number=original_post_id)


        if chat_room.starter == user:
            other_user = chat_room.receiver
        else:
            other_user = chat_room.starter

        if chat_room is None:
            messages.error(request, 'Chat room does not exist.')
            return redirect('dangun_app:trade')
        
        # buyer를 설정하고, product_sold를 Y로 설정
        post.buyer = chat_room.receiver if chat_room.starter == post.user else chat_room.starter
        post.product_sold = 'Y'
        post.save()
        
        # 거래가 확정되면 새로고침
        return redirect('dangun_app:chat_room', pk=chat_room.room_number)

# 채팅 끝 ################################################################################


# 메인 화면
def main(request):
    top_views_posts = Post.objects.filter(product_sold="N").order_by("-view_num")[:4]
    return render(request, "dangun_app/main.html", {"posts": top_views_posts})


def alert(request, alert_type):
    # alert_type에 따라 다른 템플릿 선택
    if alert_type == "login":
        template_name = "dangun_app/alert_login.html"
        alert_message = "로그인해주세요!"
    elif alert_type == "region":
        template_name = "dangun_app/alert_region.html"
        alert_message = "동네인증해주세요!"
    elif alert_type == "userProfile":
        template_name = "dangun_app/alert_userProfile.html"
        alert_message = "사용자정보가 없어요!"
    else:
        # 기본 템플릿 또는 오류 처리
        template_name = "dangun_app/alert_region.html"
        alert_message = "알 수 없는 알림 유형입니다."

    context = {}  # alert_message를 컨텍스트에 추가
    return render(request, template_name)


# 테스트용 화면
def test(request):
    return render(request, "dangun_app/test.html")


# 중고거래 화면
def trade(request):
    top_views_posts = Post.objects.filter(product_sold="N").order_by("-modified_at")
    return render(request, "dangun_app/trade.html", {"posts": top_views_posts})


# 중고거래상세정보(각 포스트) 화면
def trade_post(request, pk):
    post = get_object_or_404(Post, pk=pk)

    # 조회수 증가
    if request.user.is_authenticated:
        if request.user != post.user:
            post.view_num += 1
            post.save()
    else:
        post.view_num += 1
        post.save()

    try:
        user_profile = UserProfile.objects.get(user=post.user)
    except UserProfile.DoesNotExist:
        user_profile = None

    context = {
        "post": post,
        "user_profile": user_profile,
    }

    return render(request, "dangun_app/trade_post.html", context)


# 거래글쓰기 화면
@login_required
def write(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)

        if user_profile.region_certification == "Y":
            return render(request, "dangun_app/write.html")
        else:
            return redirect("dangun_app:alert", alert_type="region")
    except UserProfile.DoesNotExist:
        return redirect("dangun_app:alert", alert_type="userProfile")


# 거래글수정 화면
def edit(request, id):
    post = get_object_or_404(Post, id=id)
    if post:
        post.description = post.description.strip()
    if request.method == "POST":
        post.title = request.POST["title"]
        post.price = request.POST["price"]
        post.description = request.POST["description"]
        post.location = request.POST["location"]
        if "images" in request.FILES:
            new_images = request.FILES.getlist("images")
            post.images.set(new_images)  # 다대다 관계의 역방향 필드에 set() 메서드를 사용하여 업데이트합니다.
        post.save()
        return redirect("dangun_app:trade_post", pk=id)

    return render(request, "dangun_app/write.html", {"post": post})


def userprofile(request, user_id):
    user = get_object_or_404(User, username=user_id)
    id = user.id
    userprofile = get_object_or_404(UserProfile, user_id=id)

    # 로그인한 사용자인 경우
    if request.user.is_authenticated:
        # 자기 자신의 프로필 페이지인 경우 또는 공개 프로필인 경우
        if request.user == userprofile.user or userprofile.public_profile:
            if request.method == "POST":
                # 프로필 정보 수정 폼을 제출한 경우
                userprofile_form = UserProfileForm(
                    request.POST, request.FILES, instance=userprofile
                )
                if userprofile_form.is_valid():
                    userprofile_form.save()
                    return render(
                        request, "dangun_app/userprofile.html", {"userprofile": userprofile}
                    )
            else:
                # POST 요청이 아닌 경우 또는 프로필 정보 수정 폼 보기
                userprofile_form = UserProfileForm(instance=userprofile)
            return render(
                request,
                "dangun_app/userprofile.html",
                {"userprofile": userprofile, "userprofile_form": userprofile_form},
            )

    # 로그인하지 않은 사용자 또는 공개 프로필이 아닌 경우
    return render(request, "dangun_app/userprofile.html", {"userprofile": userprofile})


# def userprofile(request, user_id):
#     user = get_object_or_404(User, username=user_id)
#     id = user.id
#     userprofile = get_object_or_404(UserProfile, user_id=id)

#     context = {
#     "userprofile": userprofile,
#     }

#     if request.user.is_authenticated:
#         if request.user == userprofile.user and userprofile.user_certification == "N":
#             return render(request, "dangun_app/regist_userprofile.html")

#         else:
#             return render(request, "dangun_app/userprofile.html", context)
#     else:
#         return render(request, "dangun_app/userprofile.html", context)


# 채팅 화면
@login_required
def chat_view(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)

        if user_profile.region_certification == "Y":
            return render(request, "dangun_app/chat.html")
        else:
            return redirect("dangun_app:alert", alert_type="region")
    except UserProfile.DoesNotExist:
        return redirect("dangun_app:alert", alert_type="userProfile")


# 동네인증 화면
@login_required
def location(request):
    try:
        user_profile = UserProfile.objects.get(user_id=request.user)
        region = user_profile.region
    except UserProfile.DoesNotExist:
        region = None

    return render(request, "dangun_app/location.html", {"region": region})


# 가입 화면
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.shortcuts import render, redirect
from .forms import CustomRegistrationForm


def register(request):
    error_message = ""
    if request.method == "POST":
        form = CustomRegistrationForm(request.POST)
        username = request.POST.get("username")
        if User.objects.filter(username=username).exists():
            error_message = "이미 존재하는 아이디입니다."
        elif form.is_valid():
            password1 = form.cleaned_data["password1"]
            password2 = form.cleaned_data["password2"]

            # 비밀번호 일치 여부를 확인
            if password1 == password2:
                # 새로운 유저를 생성
                user = User.objects.create_user(username=username, password=password1)

                # 유저를 로그인 상태로 만듦
                login(request, user)

                return redirect("dangun_app:login")
            else:
                form.add_error("password2", "Passwords do not match")
    else:
        form = CustomRegistrationForm()

    return render(
        request, "registration/register.html", {"form": form, "error_message": error_message}
    )


# 로그인 화면
def custom_login(request):
    # 이미 로그인한 경우
    if request.user.is_authenticated:
        return redirect("dangun_app:main")

    else:
        form = CustomLoginForm(data=request.POST or None)
        if request.method == "POST":
            # 입력정보가 유효한 경우 각 필드 정보 가져옴
            if form.is_valid():
                username = form.cleaned_data["username"]
                password = form.cleaned_data["password"]

                # 위 정보로 사용자 인증(authenticate사용하여 superuser로 로그인 가능)
                user = authenticate(request, username=username, password=password)

                # 로그인이 성공한 경우
                if user is not None:
                    login(request, user)  # 로그인 처리 및 세션에 사용자 정보 저장
                    return redirect("dangun_app:main")  # 리다이렉션
        return render(request, "registration/login.html", {"form": form})  # 폼을 템플릿으로 전달


# 포스트 업로드
@login_required
def create_post(request):
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)  # 임시 저장
            post.user = request.user  # 작성자 정보 추가 (이 부분을 수정했습니다)
            post.save()  # 최종 저장
            return redirect("dangun_app:trade_post", pk=post.pk)  # 저장 후 상세 페이지로 이동
    else:
        form = PostForm()
    return render(request, "dangun_app/trade_post.html", {"form": form})


# 포스트 검색
def search(request):
    query = request.GET.get("search")
    if query:
        results = Post.objects.filter(Q(title__icontains=query) | Q(location__icontains=query))
    else:
        results = Post.objects.all()

    return render(request, "dangun_app/search.html", {"posts": results})


# 지역설정
@login_required
def set_region(request):
    if request.method == "POST":
        region = request.POST.get("region-setting")

        if region:
            try:
                user_profile, created = UserProfile.objects.get_or_create(user=request.user)
                user_profile.region = region
                user_profile.save()

                return redirect("dangun_app:location")
            except Exception as e:
                return JsonResponse({"status": "error", "message": str(e)})
        else:
            return JsonResponse({"status": "error", "message": "Region cannot be empty"})
    else:
        return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)


# 지역인증 완료
@login_required
def set_region_certification(request):
    if request.method == "POST":
        request.user.profile.region_certification = "Y"
        request.user.profile.save()
        messages.success(request, "인증되었습니다")
        return redirect("dangun_app:location")


def delete_post(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
        # 삭제 권한 확인
        if request.user.username == post.user.username:
            post.delete()
            # JSON 응답을 반환합니다.
            return JsonResponse({"message": "포스트가 성공적으로 삭제되었습니다."})
        else:
            # 삭제 권한이 없는 경우에 대한 처리
            return JsonResponse({"message": "삭제 권한이 없습니다."}, status=403)  # 403 Forbidden 상태 코드 반환
    except Post.DoesNotExist:
        # 포스트가 존재하지 않는 경우에 대한 처리
        return JsonResponse({"message": "포스트가 존재하지 않습니다."}, status=404)  # 404 Not Found 상태 코드 반환


# 오래된 게시글 끌어올리기 기능
from datetime import datetime, timezone


def bring_to_top(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    post.modified_at = datetime.now(timezone.utc)
    post.save()
    return redirect("dangun_app:trade")
