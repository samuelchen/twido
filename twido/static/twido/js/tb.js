var taobao = {
    urls: {
        home: 'https://taobao.com',
        login: 'https://login.taobao.com/member/login.jhtml',
        cart: 'https://cart.taobao.com/cart.htm'
    },
    patterns: {
        cart_items: 'ul.item-content',
        cart_item_img: 'img.itempic',
        cart_item_a: 'a.item-title',
        cart_item_price: 'em.J_Price .price-now'
    },

    get_items: function(parent) {
        var items = [];
        var patterns = this.patterns;
        var f = parent;
        console.debug(patterns.cart_items);
        console.debug(f.find(patterns.cart_items));
        f.find(patterns.cart_items).each(function(idx, obj){
            var img = obj.find($(patterns.cart_item_img)).attr('src');
            var a = obj.find($(patterns.cart_item_a));
            var price = obj.find($(patterns.cart_item_price)).text();
            var link = a.attr('href');
            var title = a.text();
            console.log('title:' + title + '\nprice:' + price + '\nlink:' + link + '\nimg:' + img);
            var item = {
                title: title,
                price: price,
                img: img,
                link: link
            };
            items.append(item);
        });
        return items;
    },

    padding: {

    }
};
