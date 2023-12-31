from rest_framework import viewsets, permissions, generics, response
from rest_framework.decorators import action
from rest_framework.response import Response

from account.permissions import SecondLevelPermission, FirstLevelPermission, ThirdLevelPermission
from course import serializers
from course.models import Subject, Course
from course.serializers import SubjectSerializer
from feedback.serializers import ReviewSerializer, LikeUserSerializer, RatingSerializer


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = serializers.CourseSerializer

    def get_permissions(self):
        if self.action in permissions.SAFE_METHODS:
            return [FirstLevelPermission()]
        return [SecondLevelPermission()]

    # http://127.0.0.1:8000/api/v1/course/<id>/review/
    @action(['GET'], detail=True)
    def review(self, request, pk):
        course = self.get_object()
        reviews = course.reviews.all()
        serializer = ReviewSerializer(instance=reviews, many=True)
        return Response(serializer.data, status=200)

    # http://127.0.0.1:8000/api/v1/course/id/like/
    @action(['GET'], detail=True)
    def like(self, request, pk):
        course = self.get_object()
        likes = course.likes.all()
        serializer = LikeUserSerializer(instance=likes, many=True)
        return Response(serializer.data, status=200)

    @action(['GET'], detail=True)
    def subjects(self, request, pk=None):
        course = self.get_object()
        subjects = course.subjects.all()
        serializer = SubjectSerializer(instance=subjects, many=True)
        return Response(serializer.data, status=200)

    @action(['GET'], detail=True)
    def requirements(self, request, pk=None):
        course = self.get_object()
        requirements = course.requirements.all()
        serializer = SubjectSerializer(instance=requirements, many=True)
        return Response(serializer.data, status=200)

    # http://127.0.0.1:8000/api/v1/course/id/rating/
    @action(['GET', 'POST', 'DELETE'], detail=True)
    def rating(self, request, pk):
        # permission_classes = (permissions.IsAuthenticated,)
        product = self.get_object()
        user = request.user
        is_rating = product.ratings.filter(owner=user).exists()

        if request.method == 'GET':
            ratings = product.ratings.all()
            serializer = RatingSerializer(instance=ratings, many=True)
            return response.Response(serializer.data, status=200)
        elif request.method == 'POST':
            if is_rating:
                return response.Response('You already rated this product', status=400)
            data = request.data
            serializer = RatingSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save(owner=user, product=product)
            return response.Response(serializer.data, status=201)
        else:
            if not is_rating:
                return response.Response('You did\'t rated this product', status=400)
            rating = product.ratings.get(owner=user)
            rating.delete()
            return response.Response('Deleted!', status=204)


class CourseSearchView(generics.ListAPIView):
    serializer_class = serializers.CourseSerializer
    queryset = Course.objects.all()

    def get_queryset(self):
        title = self.request.query_params.get('title')
        description = self.request.query_params.get('description')
        queryset = self.queryset

        if title:
            queryset = queryset.filter(title__icontains=title)
        elif description:
            queryset = queryset.filter(description__icontains=description)

        return queryset


class SubjectCreateListView(generics.ListCreateAPIView):
    queryset = Subject.objects.all()
    serializer_class = serializers.SubjectSerializer

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [FirstLevelPermission()]
        return [ThirdLevelPermission()]