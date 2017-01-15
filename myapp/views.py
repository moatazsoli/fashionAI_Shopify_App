from django.shortcuts import render
from shopify_auth.decorators import login_required
# Create your views here.
import shopify
from django.http import HttpResponseRedirect
from django.shortcuts import render
from myapp.forms import UploadFileForm, ImageUploadForm
import tensorflow as tf, sys
import os 

description ={
"shortdress": "Short prom dresses continue to grow in popularity and these sensational designs show you why",
"shirt": "Looking for a shirt with a trimmer fit?",
"blouses": "Check out the latest Blouses from ourshop",
"coat": "Looking for an awesome coat?",
"sweater": "sweaters and cardigans for everyone",
"cloak": "Checkout our cloak collections!",
"uniform": "Uniforms for everyone",
"jacket": "Checkout our new jacket collection!",
"tshirt": "tshirts .. simplicity ..",
"longdress": "Long dresses for elegance look and every occassion",
"suit": "Custom tailored suits for perfect fit!",
"sportshirt": "sports shirts for cool look",
"robe": "Robes",
"vest": "Vests for different occassions"
}

tags ={
"shortdress": "shortdress, elegance, outfitoftheday, fashion",
"shirt": "shirt, simple, outfitoftheday, fashion",
"blouses": "lookoftheday, blouse, fashion, simple, simplicity",
"coat": "coat, fashion, cool, pullingitoff",
"sweater": "sweaters, fashion, casual, swagger",
"cloak": "outfitoftheday, fashion",
"uniform": "uniform, overalls, outfitoftheday, fashion",
"jacket": "jacket, cold, swag, model",
"tshirt": "style, simple, swag",
"longdress": "longdress, elegance, prom, style, fashion",
"suit": "suit, fashion, model, outfitoftheday, corporate",
"sportshirt": "lookoftheday, shirt, swag",
"robe": "robe, shinebright, positive",
"vest": "vest, coollook, fashion, shine"
}

# @login_required
# def home(request,*args, **kwargs):
#     return render(request, "myapp/home.html")


# def home(request):
#     if request.method == 'POST':
#         form = UploadFileForm(request.POST, request.FILES)
#         if form.is_valid():
#             response = handle_uploaded_file(request.FILES['image'])


#             form2 = ImageUploadForm(initial={'image': request.FILES['image'] , 'title': "hihi" })
#             return render(request, 'myapp/upload.html' ,{ 'text':response['text'],
#             'closest': response['closest'] , 'form': form2} )
#     else:
#         form = UploadFileForm()
#     return render(request, 'myapp/home.html', {'form': form})

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.contrib.sites.shortcuts import get_current_site




from django.contrib import auth
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect
from django.shortcuts import render, resolve_url
def get_return_address(request):
    return request.GET.get(auth.REDIRECT_FIELD_NAME) or resolve_url(settings.LOGIN_REDIRECT_URL)

def test(request):
    shop = request.POST.get('shop', request.GET.get('shop'))

    print shop

    if shop:
        redirect_uri = request.build_absolute_uri(reverse(finalize))
        print redirect_uri
        scope = settings.SHOPIFY_APP_API_SCOPE
        permission_url = shopify.Session(shop.strip()).create_permission_url(scope, redirect_uri)
        print permission_url

        if settings.SHOPIFY_APP_IS_EMBEDDED:
            # Embedded Apps should use a Javascript redirect.
            return render(request, "shopify_auth/iframe_redirect.html", {
                'redirect_uri': permission_url
            })
        else:
            # Non-Embedded Apps should use a standard redirect.
            return HttpResponseRedirect(permission_url)

    return_address = get_return_address(request)
    print "returning"
    print return_address
    return HttpResponseRedirect(return_address)


@login_required
def home(request):
    # request = None
    print get_current_site(request).domain
    # full_url = ''.join(['http://', get_current_site(request).domain, obj.get_absolute_url()])
    if request.method == 'POST' and request.FILES['image']:
        myfile = request.FILES['image']
        fs = FileSystemStorage()
        filename = fs.save(myfile.name, myfile)
        uploaded_file_url = fs.url(filename)
        print filename
        full_path_for_file =  os.path.realpath(filename)
        print full_path_for_file
        print fs.location
        print fs.base_url
        image_path = os.path.join(fs.location,filename)

        image_data = tf.gfile.FastGFile(os.path.join(fs.location,filename), 'rb').read()

        dir_path = os.path.dirname(os.path.realpath(__file__))

    # Loads label file, strips off carriage return
        label_lines = [line.rstrip() for line 
                           in tf.gfile.GFile(os.path.join(dir_path,"retrained_labels.txt"))]

        # Unpersists graph from file
        with tf.gfile.FastGFile(os.path.join(dir_path,"retrained_graph.pb"), 'rb') as f:
            graph_def = tf.GraphDef()
            graph_def.ParseFromString(f.read())
            _ = tf.import_graph_def(graph_def, name='')

        with tf.Session() as sess:
            # Feed the image_data as input to the graph and get first prediction
            softmax_tensor = sess.graph.get_tensor_by_name('final_result:0')
            
            predictions = sess.run(softmax_tensor, \
                     {'DecodeJpeg/contents:0': image_data})
            
            # Sort to show labels of first prediction in order of confidence

            top_k = predictions[0].argsort()[-len(predictions[0]):][::-1]
            score_list_map = []
            closest = label_lines[top_k[0]]
            print closest
            for node_id in top_k:
                human_string = label_lines[node_id]
                score = predictions[0][node_id]
                score_list_map.append({"score":score , "human_string":human_string})
                print('%s (score = %.5f)' % (human_string, score))
            # return response

            return render(request, 'myapp/upload.html', {
                'uploaded_file_url': uploaded_file_url  , 'score_list_map':score_list_map,
                'tags':tags[closest], 'description':description[closest],
                'title': closest, 'imagepath': image_path
            })
        return render(request, 'myapp/home.html', {
            'uploaded_file_url': uploaded_file_url
        })
    return render(request, 'myapp/home.html')

@login_required
def upload(request):
    if request.method == 'POST':
        print request.POST
        with request.user.session:
            # products = shopify.Product.find()
            new_product = shopify.Product()
            new_product.title = request.POST['title'].capitalize()
            new_product.product_type = request.POST['title'].capitalize()
            new_product.body_html = request.POST['description']
            new_product.tags = request.POST['tags']
            image1 = shopify.Image()
            imagepath = request.POST['imagepath']
            with open(imagepath, "rb") as f:
                filename = imagepath.split("/")[-1:][0]
                # encoded = b64encode(f.read())
                image1.attach_image(f.read(), filename=filename)
                new_product.images = [image1]
                # new_product.images = [image1]
                success = new_product.save() #returns false if the record is invalid
                print success
                redirect_uri = "https://" + request.user.myshopify_domain + "/admin/products/"
                print redirect_uri
                return render(request, "shopify_auth/iframe_redirect.html", {
                'redirect_uri': redirect_uri
            })

        # <QueryDict: {u'csrfmiddlewaretoken': [u'cL1IJD8TEP8Hteh8BJt0PR9hVirYB1NRALtUxQvjUtFy2IClheWr5mjrYE6wdW6S'], u'tags': [u'longdress, elegance, prom, style, fashion'], u'description': [u'Long dresses for elegance look and every occassion'], u'uploaded_file_url': [u'/media/d1_5BE1DTo.jpg'], u'title': [u'longdress']}>
    return render(request, 'myapp/home.html')


def handle_uploaded_file(f):
    with open(f.name, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    image_data = tf.gfile.FastGFile(f.name, 'rb').read()

    dir_path = os.path.dirname(os.path.realpath(__file__))

# Loads label file, strips off carriage return
    label_lines = [line.rstrip() for line 
                       in tf.gfile.GFile(os.path.join(dir_path,"retrained_labels.txt"))]

    # Unpersists graph from file
    with tf.gfile.FastGFile(os.path.join(dir_path,"retrained_graph.pb"), 'rb') as f:
        graph_def = tf.GraphDef()
        graph_def.ParseFromString(f.read())
        _ = tf.import_graph_def(graph_def, name='')

    with tf.Session() as sess:
        # Feed the image_data as input to the graph and get first prediction
        softmax_tensor = sess.graph.get_tensor_by_name('final_result:0')
        
        predictions = sess.run(softmax_tensor, \
                 {'DecodeJpeg/contents:0': image_data})
        
        # Sort to show labels of first prediction in order of confidence

        top_k = predictions[0].argsort()[-len(predictions[0]):][::-1]
        response = {}
        text = ''
        closest = label_lines[top_k[0]]
        print closest
        for node_id in top_k:
            human_string = label_lines[node_id]
            score = predictions[0][node_id]
            print('%s (score = %.5f)' % (human_string, score))
            text += ('%s (score = %.5f)' % (human_string, score))
            text += "\n"
        response['text'] = text
        response['closest'] = closest
        return response


