from django.urls import path
from . import views
from django.conf.urls.static import static

urlpatterns = [
    path('', views.realm_list, name='realm_list'),
    #path('get-production-choices/', views.get_production_choices, name='get_production_choices'),
    # Multi-step Realm Creation Wizard
    path('create/start/', views.create_realm_start, name='create_realm_start'),  # Intro/start page
    path('create/step-1/', views.create_realm_step_1, name='create_realm_step_1'),  # Basic info
    path('create/step-2/', views.create_realm_step_2, name='create_realm_step_2'),  # Treasury
    path('create/step-3/', views.create_realm_step_3, name='create_realm_step_3'),  # Resources
    path('create/step-4/', views.create_realm_step_4, name='create_realm_step_4'),  # Land
    path('create/step-5/', views.create_realm_step_5, name='create_realm_step_5'),  # Population
    path('create/review/', views.create_realm_review, name='create_realm_review'),  # Final review
    #path('create/', views.create_realm, name='create_realm'),
    # Edit Views for new realm creation
    path('create/edit/realm-info/', views.edit_realm_info, name='edit_realm_info'),
    path('create/edit/treasury/', views.edit_treasury, name='edit_treasury'),
    path('create/edit/resources/', views.edit_resources, name='edit_resources'),
    path('create/edit/land/', views.edit_land, name='edit_land'),
    path('create/edit/population/', views.edit_population, name='edit_population'),
    # Edit Views for existing realm (new URLs for editing)
    path('<str:realm_name>/edit/realm-info/', views.edit_realm_info, name='edit_existing_realm_info'),
    path('<str:realm_name>/edit/treasury/', views.edit_treasury, name='edit_existing_treasury'),
    path('<str:realm_name>/edit/resources/', views.edit_resources, name='edit_existing_resources'),
    path('<str:realm_name>/edit/land/', views.edit_land, name='edit_existing_land'),
    path('<str:realm_name>/edit/population/', views.edit_population, name='edit_existing_population'),
    path('<str:realm_name>/actions/', views.player_actions, name='player_actions'),
    path('<str:realm_name>/end_turn/', views.end_turn, name='end_turn'),
    path('<str:realm_name>/start_action/', views.start_action, name='start_action'),  # Add this line
    # Other existing URLs for realm detail and creation of land and population units
    path('realm_scales_json/', views.get_realm_scales_json, name='get_realm_scales_json'),
    path('<str:name>/', views.realm_detail, name='realm_detail'),
    path('realms/<str:name>/delete/', views.delete_realm, name='delete_realm'),
    path('<str:realm_name>/create_land_unit/', views.create_land_unit, name='create_land_unit'),
    path('<str:realm_name>/create_population_unit/', views.create_population_unit, name='create_population_unit'),
    path('realms/create/automatic/', views.realm_create_automatic, name='realm_create_automatic'),
]