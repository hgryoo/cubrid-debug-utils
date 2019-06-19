const path = require('path');
const webpack = require('webpack');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const CleanWebpackPlugin = require('clean-webpack-plugin');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const MiniCssExtractPlugin = require("mini-css-extract-plugin");

module.exports = {

  context: path.join(process.cwd(), 'src'), //the home directory for webpack

  devtool: 'source-map', // enhance debugging by adding meta info for the browser devtools

  entry: {
    app: './index.js'
  },

  optimization: {
    splitChunks: {
        cacheGroups: {
            default: false,
            vendors: false,
            // vendor chunk
            vendor: {
                // sync + async chunks
                chunks: 'all',
                // import file path containing node_modules
                test: /node_modules/
            }
        }
    }
  },

  output: {
    path: path.join(process.cwd(), 'dist'),
    filename: '[name].[hash].js',
    publicPath: '/',
    sourceMapFilename: '[name].map'
  },

  resolve: {
    extensions: ['.js'],  // extensions that are used
    modules: [path.join(process.cwd(), 'src'), 'node_modules'] // directories where to look for modules
  },

  module: {
    rules: [{
      enforce: "pre", //to check source files, not modified by other loaders (like babel-loader)
      test: /\.js$/,
      exclude: /node_modules/
      //loader: "eslint-loader"
    }, {
      test: /\.js$/,
      exclude: /node_modules/,
      use: {
        loader: 'babel-loader',
        options: {
          presets: ['env']
        }
      }
    },{
      test: /\.(sa|sc|c)ss$/,
      use: [
        {
          loader: MiniCssExtractPlugin.loader,
          options: {
            hmr: process.env.NODE_ENV === 'development',
          },
        },
        'css-loader',
        {
          loader: 'postcss-loader', // Run post css actions
          options: {
            plugins: function () { // post css plugins, can be exported to postcss.config.js
              return [
                require('precss'),
                require('autoprefixer')
              ];
            }
          }
        },
        'sass-loader',
      ],
    }]
  },
  plugins: [
    new CleanWebpackPlugin(['dist'], {root: process.cwd()}),
    new CopyWebpackPlugin ([
      {
        from: 'static',
        to: 'static'
      }
    ]),
    new HtmlWebpackPlugin({
      template: 'index.html'
    }),
    new MiniCssExtractPlugin({
      filename: "[name].[contenthash].css"
    })
  ]
};