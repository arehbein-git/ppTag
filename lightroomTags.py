import xml.dom.minidom

def parse_xmp_for_lightroom_tags(xmp_string):
    data = {}
    data['rating'] = 0
    data['tags'] = []
    xmlDocument = xml.dom.minidom.parseString(xmp_string)
    xmp = xmlDocument.documentElement
    if xmp.hasAttribute('xmlns:x'):
        if xmp.getAttribute('xmlns:x') == 'adobe:ns:meta/':
            # this is adobe meta data so continue
            rdf = xmp.getElementsByTagName('rdf:RDF')[0]
            desc = rdf.getElementsByTagName('rdf:Description')[0]
            rating = desc.getAttribute('xmp:rating')
            
            if desc.hasAttribute('xmp:Rating'):
                rating = desc.getAttribute('xmp:Rating')
                data['rating'] = int(rating)
            subject = desc.getElementsByTagName('dc:subject')[0]
            bag = subject.getElementsByTagName('rdf:Bag')[0]
            lightroomTags = bag.getElementsByTagName('rdf:li')
            tagsCombinedArray = []
            for tags in lightroomTags:
                tag = tags.firstChild.nodeValue
                #print(tag)
                tagsCombinedArray.append(tag)

            if len(tagsCombinedArray):
                data['tags'] = tagsCombinedArray
    return data