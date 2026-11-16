from rest_framework import serializers

class AdminLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, min_length=6, write_only=True)

class AdminCreateUserSerializer(serializers.Serializer):
    name = serializers.CharField(required=True, max_length=120)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, min_length=8, write_only=True)
    role = serializers.ChoiceField(choices=["user", "admin"], default="user")
    isVerified = serializers.BooleanField(default=True)
    isPremium = serializers.BooleanField(default=False)

class AdminUpdateUserSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, max_length=120)
    role = serializers.ChoiceField(choices=["user", "admin"], required=False)
    isVerified = serializers.BooleanField(required=False)
    isPremium = serializers.BooleanField(required=False)
    isSuspended = serializers.BooleanField(required=False)
    password = serializers.CharField(required=False, min_length=8, write_only=True, allow_blank=True)

class AdminReviewFactCheckSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=["CONFIRMED", "CONTESTED", "ARCHIVED"], required=True)
    notes = serializers.CharField(required=True, max_length=2000)

class AdminNewsSerializer(serializers.Serializer):
    title = serializers.CharField(required=True, max_length=300)
    description = serializers.CharField(required=False, allow_blank=True)
    url = serializers.CharField(required=False, allow_blank=True)
    image = serializers.CharField(required=False, allow_blank=True)
    source = serializers.CharField(required=False, max_length=120, default="TruthScan Wire")
    category = serializers.CharField(required=False, max_length=80, default="General")
    isPublished = serializers.BooleanField(default=True)

class AdminCategorySerializer(serializers.Serializer):
    name = serializers.CharField(required=True, max_length=80)
    description = serializers.CharField(required=False, allow_blank=True)
    color = serializers.CharField(required=False, max_length=20, default="#3B82F6")
    icon = serializers.CharField(required=False, max_length=40, default="folder")
    isActive = serializers.BooleanField(default=True)

class AdminDeleteCategorySerializer(serializers.Serializer):
    reassignToSlug = serializers.CharField(required=False, allow_blank=True)

class AdminSettingsSerializer(serializers.Serializer):
    theme = serializers.ChoiceField(choices=["navy", "dark", "charcoal"], required=False)
    dashboardDateDefault = serializers.ChoiceField(choices=["7d", "30d", "90d", "all"], required=False)
    emailAlerts = serializers.BooleanField(required=False)
    notifyOnNewUser = serializers.BooleanField(required=False)
    notifyOnFailedAi = serializers.BooleanField(required=False)
    autoRefreshInterval = serializers.IntegerField(required=False, min_value=10, max_value=300)

class AdminChangePasswordSerializer(serializers.Serializer):
    currentPassword = serializers.CharField(required=True, write_only=True)
    newPassword = serializers.CharField(required=True, min_length=8, write_only=True)
