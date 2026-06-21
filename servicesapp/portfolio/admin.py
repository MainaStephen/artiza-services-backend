# portfolio/admin.py
from django.contrib import admin
from .models import WorkerPortfolio, PortfolioImage


class PortfolioImageInline(admin.TabularInline):
    model = PortfolioImage
    extra = 0
    fields = ('image', 'title', 'description', 'order')


@admin.register(WorkerPortfolio)
class WorkerPortfolioAdmin(admin.ModelAdmin):
    list_display = ['worker', 'professional_title', 'completed_projects_count', 'average_rating', 'availability']
    list_filter = ['availability', 'is_active', 'created_at']
    search_fields = ['worker__full_name', 'worker__email', 'professional_title']
    readonly_fields = ['completed_projects_count', 'average_rating', 'total_reviews']
    inlines = [PortfolioImageInline]
    
    fieldsets = (
        ('Worker Information', {
            'fields': ('worker', 'professional_title', 'bio')
        }),
        ('Skills & Service', {
            'fields': ('skills', 'service_area', 'hourly_rate', 'availability')
        }),
        ('Images', {
            'fields': ('profile_image', 'cover_image')
        }),
        ('Social Links', {
            'fields': ('website', 'facebook', 'instagram'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('completed_projects_count', 'average_rating', 'total_reviews', 'is_active'),
            'classes': ('collapse',)
        }),
    )
    
    def completed_projects_count(self, obj):
        return obj.completed_projects_count
    completed_projects_count.short_description = 'Completed Projects'
    
    def average_rating(self, obj):
        return f"{obj.average_rating} ⭐" if obj.average_rating else "No ratings"
    average_rating.short_description = 'Rating'


@admin.register(PortfolioImage)
class PortfolioImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'portfolio', 'title', 'order', 'created_at']
    list_filter = ['created_at']
    search_fields = ['portfolio__worker__full_name', 'title']